import uuid
from typing import Annotated, List

from pydantic import BaseModel
from pydantic.v1 import Field

from src.transactions.schemas import TransactionResponse
from src.users.models import Plans


class SuccessfulResponse(BaseModel):
    success: str = "ok"


class SuccessfulGetVerifyCodeResponse(BaseModel):
    success: str = "The verify code has been successfully sent to the email"


class SuccessfulValidation(BaseModel):
    success: str = "Successful Validation!"


class TokenData(BaseModel):
    email: str | None = None


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"


class UserCreate(BaseModel):
    email: Annotated[str, Field(min_length=6, max_length=50)]
    password: Annotated[str, Field(min_length=8, max_length=25)]


class UserResponse(BaseModel):
    id: uuid.UUID
    email: Annotated[str, Field(min_length=6, max_length=50)]
    plan: Plans
    message_length_limit: int
    message_count_limit: int

    class Config:
        orm_mode = True
