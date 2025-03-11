import secrets
import smtplib
import uuid
from urllib.parse import urlencode

import httpx
import jwt

from datetime import timedelta
from typing import Optional, Dict
from fastapi import Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config_data.config import Config, load_config
from utils.auth_settings import validate_password, decode_jwt, encode_jwt
from fastapi.responses import RedirectResponse

from src.users.models import User, OAuthProvider
from src.users.repositories import UserRepository
from src.users.schemas import UserCreate, TokenData
from src.users.exceptions import CredentialException, TokenTypeException, NotFoundException, AccessException, \
    EmailExistsException, IncorrectEmailAddressException, IncorrectVerifyCodeException, EmailSenderException
from utils.email_sender import send_verification_code

http_bearer = HTTPBearer()

settings: Config = load_config(".env")
auth_config = settings.authJWT
google_config = settings.googleData
yandex_config = settings.yandexData
github_config = settings.githubData

oauth_config_data = {
    "google": google_config,
    "yandex": yandex_config,
    "github": github_config
}

TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USER_INFO_URL = "https://login.yandex.ru/info"

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


class UserService:
    repository = UserRepository()

    async def get_google_oauth_email(self, data: Dict) -> str:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(OAuthProvider.GOOGLE.value["TOKEN_URL"], data=data)
            token_response.raise_for_status()
            tokens = token_response.json()

        async with httpx.AsyncClient() as client:
            people_response = await client.get(
                OAuthProvider.GOOGLE.value["USER_URL"],
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            people_response.raise_for_status()
            user_info = people_response.json()

        return user_info["emailAddresses"][0]["value"]

    async def get_yandex_oauth_email(self, data: Dict) -> str:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(OAuthProvider.YANDEX.value["USER_URL"], data=data)
            token_response.raise_for_status()
            tokens = token_response.json()

        async with httpx.AsyncClient() as client:
            user_info_response = await client.get(
                OAuthProvider.GOOGLE.value["USER_URL"],
                headers={"Authorization": f"OAuth {tokens['access_token']}"},
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()

        return user_info["default_email"]

    async def get_github_oauth_email(self, data: Dict) -> str:
        headers = {
            "Accept": "application/json",
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(OAuthProvider.GITHUB.value["TOKEN_URL"], params=data, headers=headers)
                response.raise_for_status()
                tokens = response.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=400, detail="Failed to obtain tokens from GitHub")

        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Invalid token response from GitHub")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient() as client:
            try:
                user_response = await client.get(OAuthProvider.GITHUB.value["USER_URL"], headers=headers)
                user_response.raise_for_status()

                email_response = await client.get("https://api.github.com/user/emails", headers=headers)
                email_response.raise_for_status()
                emails = email_response.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(status_code=400, detail="Failed to fetch user info from GitHub")

        primary_email = next((email["email"] for email in emails if email["primary"]), None)

        return primary_email

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
                email = await self.get_google_oauth_email(data)
            case "yandex":
                email = await  self.get_yandex_oauth_email(data)
            case "github":
                email = await self.get_github_oauth_email(data)
            case _:
                raise HTTPException(status_code=403, detail="Service not allowed")

        user_data = {
            "email": email,
            "password": secrets.token_urlsafe(16)
        }

        try:
            user = await self.get_user_by_email(user_data["email"])
        except NotFoundException:
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
