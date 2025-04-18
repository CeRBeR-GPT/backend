import datetime
import secrets
import uuid
import random
import jwt
import logging

from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from datetime import timedelta
from urllib.parse import urlencode
from typing import Optional, List

from src.users.models import User, OAuthProvider, Plans, Feedback, CodeType
from src.users.repositories import UserRepository
from src.users.schemas import UserCreate, TokenData, UserLogin, FeedbackCreate
from src.users.exceptions import CredentialException, TokenTypeException, UserNotFoundException, AccessException, \
    EmailExistsException, IncorrectEmailAddressException, IncorrectVerifyCodeException, EmailSenderException, \
    OAuthServiceNotFoundException, InvalidOAuthStateException, CodeTypeException

from statistic.schemas import UserDocument, DayStatistic
from statistic.utils import get_or_create_user
from tasks.celery_worker import task_send_to_email

from config_data.constants import messages
from config_data.config import Config, load_config

from utils.jwt_settings import validate_password, decode_jwt, encode_jwt
from utils.oauth2_settings import get_google_oauth_email, get_yandex_oauth_email, get_github_oauth_email

http_bearer = HTTPBearer()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings: Config = load_config(".env")
auth_config = settings.authJWT
variables = settings.variablesData
email_sender = settings.email_sender

TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class UserService:
    repository = UserRepository()

    @staticmethod
    def generate_confirmation_mode():
        return random.randint(email_sender.MIN_CODE, email_sender.MAX_CODE)

    async def get_oauth2_redirect(self, request: Request, service: OAuthProvider) -> RedirectResponse:
        service_data = service.value
        state = secrets.token_urlsafe(32)
        request.session[f"{service_data['name']}_oauth_state"] = state
        redirect_uri = f"{variables.CLIENT_PROTOCOL}://{variables.BACKEND_DOMAIN}/auth/{service_data['name']}/callback"

        logger.info(f"Generating OAuth2 redirect URL for {service_data['name']} service")
        logger.info(f"State: {state}")
        logger.info(f"Redirect URI: {redirect_uri}")

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
        logger.info(f"Auth URL: {auth_url}")

        return RedirectResponse(auth_url)

    async def get_response_from_oauth2_callback(
            self, request: Request, code: str, state: str, service: OAuthProvider
    ) -> RedirectResponse:
        logger.info(f"Received OAuth2 callback with code: {code} and state: {state}")

        if state != request.query_params.get("state"):
            logger.error("Error: Invalid OAuth state!")
            raise InvalidOAuthStateException()

        service_data = service.value

        data = {
            "code": code,
            "client_id": service_data["CLIENT_ID"],
            "client_secret": service_data["CLIENT_SECRET"],
            "redirect_uri": (
                f"{variables.CLIENT_PROTOCOL}://{variables.BACKEND_DOMAIN}/auth/{service_data['name']}/callback"
            ),
            "grant_type": "authorization_code",
        }

        logger.info(f"data[redirect_uri] = {data['redirect_uri']}")

        match service_data["name"]:
            case "google":
                email = await get_google_oauth_email(data)
            case "yandex":
                email = await get_yandex_oauth_email(data)
            case "github":
                email = await get_github_oauth_email(data)
            case _:
                logger.error("Error: Unknown service???")
                raise OAuthServiceNotFoundException()

        logger.info(f"Successful get user email: {email}")

        user_data = {
            "email": email,
            "password": secrets.token_urlsafe(16)
        }

        try:
            user = await self.get_user_by_email(user_data["email"])
            logger.info(f"Oauth2 user with email {user_data['email']} existed. Login...")
        except UserNotFoundException:
            logger.info(f"Oauth2 user with email {user_data['email']} not found. Registration...")
            user = await self.create_user(UserCreate(**user_data))

        access_token = self.create_access_token(user)
        refresh_token = self.create_refresh_token(user)

        logger.info(f"Creating access and refresh tokens for user {user.email}")

        response = RedirectResponse(url=settings.variablesData.FRONTEND_REDIRECT_URL)
        response.set_cookie(key="access_token", value=access_token, httponly=False, secure=True, samesite="none",
                            domain=".energy-cerber.ru")
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=False, secure=True, samesite="none",
                            domain=".energy-cerber.ru")

        logger.info(f"Successful setting cookies for access_token and refresh_token")

        return response

    async def send_feedback(self, new_feedback: FeedbackCreate, user: User) -> Feedback:
        message = messages.LETTER_FEEDBACK_MESSAGE.format(from_email=user.email, message=new_feedback.message)
        try:
            task_send_to_email.delay(
                subject=messages.LETTER_FEEDBACK_TITLE.format(name=new_feedback.name),
                body=message,
                address=email_sender.ADMIN_EMAIL
            )
        except Exception:
            raise EmailSenderException()

        return await self.repository.create_feedback(new_feedback, user.email)

    async def get_registration_verify_code(self, email: str) -> None:
        potential_user = await self.repository.get_user_by_email(email)
        if potential_user is not None:
            raise EmailExistsException()

        code = self.generate_confirmation_mode()
        message = messages.LETTER_CONFIRMATION_MESSAGE.format(code=code)
        potential_code = await self.repository.get_verify_code_by_email(email)
        if potential_code is not None:
            await self.repository.update_verify_code(email, code, CodeType.for_registration)
        else:
            await self.repository.create_verify_code(email, code, CodeType.for_registration)

        try:
            task_send_to_email.delay(
                subject=messages.LETTER_REGISTRATION_TITLE,
                body=message,
                address=email
            )
        except Exception:
            raise EmailSenderException()

    async def get_edit_password_verify_code(self, user: User) -> None:
        code = self.generate_confirmation_mode()
        message = messages.LETTER_CONFIRMATION_MESSAGE.format(code=code)
        potential_code = await self.repository.get_verify_code_by_email(user.email)
        if potential_code is not None:
            await self.repository.update_verify_code(user.email, code, CodeType.for_reset_password)
        else:
            await self.repository.create_verify_code(user.email, code, CodeType.for_reset_password)

        try:
            task_send_to_email.delay(
                subject=messages.LETTER_PASSWORD_RESET_TITLE,
                body=message,
                address=user.email
            )
        except Exception:
            raise EmailSenderException()

    async def check_verify_code(self, email: str, code: int, excepted_type: CodeType) -> bool:
        verify_code = await self.repository.get_verify_code_by_email(email)

        if verify_code.type != excepted_type:
            raise CodeTypeException(verify_code.type.value, excepted_type.value)
        if verify_code is None:
            raise IncorrectEmailAddressException()
        if verify_code.code != code:
            raise IncorrectVerifyCodeException()

        await self.repository.delete_verify_code_by_id(verify_code.id)

        return True

    async def get_user_statistic(self, user: User) -> List[DayStatistic]:
        mongo_user: UserDocument = await get_or_create_user(user_id=user.id)
        return mongo_user.statistics

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

    async def authenticate_user(self, user_data: UserLogin) -> Optional[User]:
        user = await self.repository.get_user_by_email(user_data.email)
        if not user:
            raise CredentialException()
        if not validate_password(user_data.password, user.password_hash):
            raise CredentialException()

        return user

    async def validate_user(self, expected_token_type: str = ACCESS_TOKEN_TYPE, token: str | bytes = "") -> User:

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

        new_user = await self.repository.create_user(user)

        from src.ai_chat.services import AIChatService
        from src.ai_chat.models import MessageBelong

        welcome_chat = await AIChatService().create_new_chat(new_user, messages.WELCOME_CHAT_NAME)
        await AIChatService().create_new_message(
            new_user, messages.WELCOME_CHAT_MESSAGE, welcome_chat.id, MessageBelong.assistant_message
        )

        return new_user

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

    async def update_user_plan(self, user_id: uuid.UUID, plan: Plans, plan_expire_date: datetime.date) -> User:
        return await self.repository.update_user_plan(user_id, plan, plan_expire_date)

    async def change_verified_status(self, user_id: uuid.UUID) -> User:
        user = await self.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundException()
        if user.is_admin:
            raise AccessException()

        return await self.repository.change_verified_status(user)
