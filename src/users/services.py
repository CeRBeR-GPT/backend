import secrets
import smtplib
import uuid
import jwt

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from datetime import timedelta
from urllib.parse import urlencode
from typing import Optional

from src.users.models import User, OAuthProvider, Plans
from src.users.repositories import UserRepository
from src.users.schemas import UserCreate, TokenData
from src.users.exceptions import CredentialException, TokenTypeException, UserNotFoundException, AccessException, \
    EmailExistsException, IncorrectEmailAddressException, IncorrectVerifyCodeException, EmailSenderException, \
    OAuthServiceNotFoundException, InvalidOAuthStateException
from utils.email_sender import send_verification_code

from config_data.config import Config, load_config
from utils.jwt_settings import validate_password, decode_jwt, encode_jwt
from utils.oauth2_settings import get_google_oauth_email, get_yandex_oauth_email, get_github_oauth_email

http_bearer = HTTPBearer()

settings: Config = load_config(".env")
auth_config = settings.authJWT

TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class UserService:
    repository = UserRepository()

    async def get_oauth2_redirect(self, request: Request, service: OAuthProvider) -> RedirectResponse:
        service_data = service.value
        state = secrets.token_urlsafe(32)
        request.session[f"{service_data['name']}_oauth_state"] = state
        redirect_uri = request.url_for(f"{service_data['name']}_callback")

        params = {
            "client_id": service_data['CLIENT_ID'],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": service_data['scope'],
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }

        auth_url = f"{service_data['AUTH_URL']}?{urlencode(params)}"
        return RedirectResponse(auth_url)

    async def get_response_from_oauth2_callback(
            self, request: Request, code: str, state: str, service: OAuthProvider
    ) -> RedirectResponse:
        if state != request.query_params.get("state"):
            raise InvalidOAuthStateException()

        service_data = service.value

        data = {
            "code": code,
            "client_id": service_data["CLIENT_ID"],
            "client_secret": service_data["CLIENT_SECRET"],
            "redirect_uri": request.url_for(f"{service_data['name']}_callback"),
            "grant_type": "authorization_code",
        }

        match service_data["name"]:
            case "google":
                email = await get_google_oauth_email(data)
            case "yandex":
                email = await get_yandex_oauth_email(data)
            case "github":
                email = await get_github_oauth_email(data)
            case _:
                raise OAuthServiceNotFoundException()

        user_data = {
            "email": email,
            "password": secrets.token_urlsafe(16)
        }

        try:
            user = await self.get_user_by_email(user_data["email"])
        except UserNotFoundException:
            user = await self.create_user(UserCreate(**user_data))

        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)

        response = RedirectResponse(url=settings.variablesData.FRONTEND_REDIRECT_URL)
        response.set_cookie(key="access_token", value=access_token, httponly=False, secure=True, samesite="none",
                            domain=".energy-cerber.ru")
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=False, secure=True, samesite="none",
                            domain=".energy-cerber.ru")

        return response

    async def get_verify_code(self, email: str) -> None:
        potential_user = await self.repository.get_user_by_email(email)
        if potential_user is not None:
            raise EmailExistsException()

        try:
            code = send_verification_code(email)
            potential_code = await self.repository.get_verify_code_by_email(email)
            if potential_code is not None:
                await self.repository.update_verify_code(email, code)
            else:
                await self.repository.create_verify_code(email, code)

        except smtplib.SMTPRecipientsRefused as e:
            raise IncorrectEmailAddressException()
        except Exception as e:
            raise EmailSenderException()

    async def check_verify_code(self, email: str, code: int) -> bool:
        verify_code = await self.repository.get_verify_code_by_email(email)
        if verify_code is None:
            raise IncorrectEmailAddressException()

        if verify_code.code != code:
            raise IncorrectVerifyCodeException()

        await self.repository.delete_verify_code_by_id(verify_code.id)
        return True

    @staticmethod
    def create_jwt(
            token_type: str,
            token_data: dict,
            expire_minutes: int = auth_config.access_token_expire_minutes,
            expire_timedelta: timedelta | None = None
    ) -> str:
        jwt_payload = {TOKEN_TYPE_FIELD: token_type}
        jwt_payload.update(token_data)
        token = encode_jwt(
            payload=jwt_payload,
            expire_minutes=expire_minutes,
            expire_timedelta=expire_timedelta
        )
        return token

    def create_access_token(self, user: User) -> str:
        jwt_payload = {
            "sub": user.email,
            "uuid": str(user.user_tokens_id)
        }
        return self.create_jwt(
            token_type=ACCESS_TOKEN_TYPE,
            token_data=jwt_payload,
            expire_minutes=auth_config.access_token_expire_minutes
        )

    def create_refresh_token(self, user: User) -> str:
        jwt_payload = {
            "sub": user.email,
            "uuid": str(user.user_tokens_id)
        }
        return self.create_jwt(
            token_type=REFRESH_TOKEN_TYPE,
            token_data=jwt_payload,
            expire_timedelta=timedelta(days=auth_config.refresh_token_expire_days)
        )

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.repository.get_user_by_email(email)
        if not user:
            raise CredentialException()
        if not validate_password(password, user.password_hash):
            raise CredentialException()

        return user

    async def validate_user(self, expected_token_type: str, token: str | bytes) -> User:

        try:
            payload = decode_jwt(token=token)
            token_type = payload.get(TOKEN_TYPE_FIELD)
            if token_type != expected_token_type:
                raise TokenTypeException(token_type, expected_token_type)

            email: str = payload.get("sub")
            tokens_id = uuid.UUID(payload.get("uuid"))
            if email is None:
                raise CredentialException()
            token_data = TokenData(email=email)

        except jwt.DecodeError:
            raise CredentialException()
        except jwt.ExpiredSignatureError:
            raise CredentialException()

        user = await self.repository.get_user_by_email(token_data.email)
        if user is None or user.user_tokens_id != tokens_id:
            raise CredentialException()

        return user

    async def create_user(self, user: UserCreate) -> User:
        if await self.repository.get_user_by_email(user.email) is not None:
            raise EmailExistsException()

        return await self.repository.create_user(user)

    async def edit_user_password(self, user: User, password: str) -> User:
        return await self.repository.edit_password(user, password)

    async def delete_user(self, user: User) -> None:
        return await self.repository.delete_user(user)

    async def get_current_user_for_refresh(self, token: HTTPAuthorizationCredentials = Depends(http_bearer)) -> User:
        return await self.validate_user(expected_token_type=REFRESH_TOKEN_TYPE, token=token.credentials)

    async def get_current_user(self, token: HTTPAuthorizationCredentials = Depends(http_bearer)) -> User:
        return await self.validate_user(expected_token_type=ACCESS_TOKEN_TYPE, token=token.credentials)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        user = await self.repository.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException()
        return user

    async def get_user_by_email(self, email: str) -> User:
        user = await self.repository.get_user_by_email(email)
        if user is None:
            raise UserNotFoundException()
        return user

    async def update_user_plan(self, user_id: uuid.UUID, plan: Plans) -> User:
        return await self.repository.update_user_plan(user_id, plan)

    async def change_verified_status(self, user_id: uuid.UUID) -> User:
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException()
        if user.is_admin:
            raise AccessException()

        return await self.repository.change_verified_status(user)
