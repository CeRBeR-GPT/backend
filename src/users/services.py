import secrets
import smtplib
import uuid
from urllib.parse import urlencode

import httpx
import jwt

from datetime import timedelta
from typing import Optional
from fastapi import Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config_data.config import Config, load_config
from utils.auth_settings import validate_password, decode_jwt, encode_jwt
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer

from src.users.models import User
from src.users.repositories import UserRepository
from src.users.schemas import UserCreate, TokenData, Token
from src.users.exceptions import CredentialException, TokenTypeException, NotFoundException, AccessException, \
    EmailExistsException, IncorrectEmailAddressException, IncorrectVerifyCodeException, EmailSenderException
from utils.email_sender import send_verification_code

http_bearer = HTTPBearer()

settings: Config = load_config(".env")
auth_config = settings.authJWT
google_config = settings.googleData

TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class UserService:
    repository = UserRepository()

    async def get_google_redirect(self, request: Request):
        state = secrets.token_urlsafe(32)
        request.session["google_oauth_state"] = state
        print(state)
        redirect_uri = request.url_for('google_callback')
        # redirect_uri = GOOGLE_REDIRECT_URL

        scope = ["openid", "email", "profile"]

        params = {
            "client_id": google_config.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scope),
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }

        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        return RedirectResponse(url)

    async def get_response_from_google_callback(self, request: Request, code: str, state: str):

        # CSRF protection
        if state != request.query_params.get("state"):
            raise HTTPException(status_code=400, detail="Invalid state")

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": google_config.GOOGLE_CLIENT_ID,
            "client_secret": google_config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": request.url_for('google_callback'),
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=data)
            token_response.raise_for_status()
            tokens = token_response.json()

        access_token = tokens["access_token"]
        people_url = "https://people.googleapis.com/v1/people/me?personFields=emailAddresses,names"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            people_response = await client.get(people_url, headers=headers)
            people_response.raise_for_status()
            user_info = people_response.json()

        user_data = {
            "email": user_info["emailAddresses"][0]["value"],
            "password": secrets.token_urlsafe(16)
        }

        try:
            user = await self.get_user_by_email(user_data["email"])
        except NotFoundException:
            user = await self.create_user(UserCreate(**user_data))

        access_token = UserService().create_access_token(user)
        refresh_token = UserService().create_refresh_token(user)

        response = RedirectResponse(url=google_config.FRONTEND_GOOGLE_URL)
        response.set_cookie(key="access_token", value=access_token)
        response.set_cookie(key="refresh_token", value=refresh_token)

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
        }
        return self.create_jwt(
            token_type=ACCESS_TOKEN_TYPE,
            token_data=jwt_payload,
            expire_minutes=auth_config.access_token_expire_minutes
        )

    def create_refresh_token(self, user: User) -> str:
        jwt_payload = {
            "sub": user.email
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
            if email is None:
                raise CredentialException()
            token_data = TokenData(email=email)

        except jwt.DecodeError:
            raise CredentialException()
        except jwt.ExpiredSignatureError:
            raise CredentialException()

        user = await self.repository.get_user_by_email(token_data.email)
        if user is None:
            raise CredentialException()

        return user

    async def create_user(self, user: UserCreate) -> User:
        if await self.repository.get_user_by_email(user.email) is not None:
            raise EmailExistsException()

        return await self.repository.create_user(user)

    async def edit_user_password(self, user: User, password: str) -> None:
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
            raise NotFoundException()
        return user

    async def get_user_by_email(self, email: str) -> User:
        user = await self.repository.get_user_by_email(email)
        if user is None:
            raise NotFoundException()
        return user

    async def change_verified_status(self, user_id: uuid.UUID) -> User:
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise NotFoundException()
        if user.is_admin:
            raise AccessException()

        return await self.repository.change_verified_status(user)
