from fastapi import APIRouter, Depends, Request
from typing import Annotated

from src.users.models import User, OAuthProvider, CodeType
from src.users.schemas import UserCreate, Token, UserResponse, SuccessfulResponse, SuccessfulGetVerifyCodeResponse, \
    SuccessfulValidation, FeedbackResponse, FeedbackCreate
from src.users.services import UserService

router = APIRouter(tags=["user"], prefix="/user")
auth_router = APIRouter(tags=["OAuth2"], prefix="/auth")


@auth_router.get("/google")
async def google_auth(request: Request):
    return await UserService().get_oauth2_redirect(request, OAuthProvider.GOOGLE)


@auth_router.get("/yandex")
async def yandex_auth(request: Request):
    return await UserService().get_oauth2_redirect(request, OAuthProvider.YANDEX)


@auth_router.get("/github")
async def github_auth(request: Request):
    return await UserService().get_oauth2_redirect(request, OAuthProvider.GITHUB)


@auth_router.get("/google/callback", name="google_callback")
async def google_auth_callback(request: Request, code: str, state: str):
    return await UserService().get_response_from_oauth2_callback(request, code, state, OAuthProvider.GOOGLE)


@auth_router.get("/yandex/callback", name="yandex_callback")
async def yandex_auth_callback(request: Request, code: str, state: str):
    return await UserService().get_response_from_oauth2_callback(request, code, state, OAuthProvider.YANDEX)


@auth_router.get("/github/callback", name="github_callback")
async def github_auth_callback(request: Request, code: str, state: str):
    return await UserService().get_response_from_oauth2_callback(request, code, state, OAuthProvider.GITHUB)


@router.get("/register/verify_code", response_model=SuccessfulGetVerifyCodeResponse)
async def get_verify_code_by_email(email: str) -> SuccessfulGetVerifyCodeResponse:
    await UserService().get_registration_verify_code(email)
    return SuccessfulGetVerifyCodeResponse()


@router.post("/register/verify_code", response_model=SuccessfulValidation)
async def check_code_from_email(email: str, code: int) -> SuccessfulValidation:
    if await UserService().check_verify_code(email, code, CodeType.for_registration):
        return SuccessfulValidation()


@router.post("/feedback", response_model=FeedbackResponse)
async def send_feedback(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        new_feedback: FeedbackCreate
) -> FeedbackResponse:
    feedback = await UserService().send_feedback(new_feedback, current_user)
    return FeedbackResponse(**feedback.to_dict())


@router.post("/register")
async def register(user_create: UserCreate) -> Token:
    user = await UserService().create_user(user_create)
    access_token = UserService().create_access_token(user)
    refresh_token = UserService().create_refresh_token(user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
async def authenticate_user_jwt(user: User = Depends(UserService().authenticate_user)) -> Token:
    access_token = UserService().create_access_token(user)
    refresh_token = UserService().create_refresh_token(user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token, response_model_exclude_none=True)
async def refresh_jwt(
        user: Annotated[User, Depends(UserService().get_current_user_for_refresh)]
) -> Token:
    access_token = UserService().create_access_token(user)
    return Token(access_token=access_token)


@router.post("/edit_password", response_model=Token)
async def edit_user_password(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        new_password: str
) -> Token:
    user = await UserService().edit_user_password(current_user, new_password)
    access_token = UserService().create_access_token(user)
    refresh_token = UserService().create_refresh_token(user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/secure_verify_code")
async def get_verify_code_by_email(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
) -> SuccessfulGetVerifyCodeResponse:
    await UserService().get_edit_password_verify_code(current_user)
    return SuccessfulGetVerifyCodeResponse()


@router.post("/secure_verify_code", response_model=SuccessfulValidation)
async def check_code_from_email(
        current_user: Annotated[User, Depends(UserService().get_current_user)],  # noqa
        email: str, code: int
) -> SuccessfulValidation:
    if await UserService().check_verify_code(email, code, CodeType.for_reset_password):
        return SuccessfulValidation()


@router.get("/self", response_model=UserResponse)
async def login_for_access_token(
        current_user: Annotated[User, Depends(UserService().get_current_user)]
) -> UserResponse:
    user_dict = current_user.to_dict()
    user_dict["statistics"] = await UserService().get_user_statistic(current_user)
    return UserResponse(**user_dict)
