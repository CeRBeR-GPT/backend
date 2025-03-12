from fastapi import APIRouter, Depends, Request
from typing import Annotated

from src.transactions.schemas import TransactionResponse
from src.users.models import User, OAuthProvider
from src.users.schemas import UserCreate, Token, UserResponse, SuccessfulResponse, SuccessfulGetVerifyCodeResponse, \
    SuccessfulValidation
from src.users.services import UserService

router = APIRouter(tags=["transaction"], prefix="/transaction")


@router.post("/payment", response_model=TransactionResponse)
async def new_payment():
    pass
