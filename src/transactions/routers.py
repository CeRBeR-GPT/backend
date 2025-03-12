import uuid

from fastapi import APIRouter, Depends, Request
from typing import Annotated, List

from src.transactions.schemas import TransactionResponse, TransactionURLResponse, CheckConfirmedResponse
from src.transactions.services import TransactionService

from src.users.models import User, Plans
from src.users.services import UserService

router = APIRouter(tags=["transaction"], prefix="/transaction")


@router.get("/all", response_model=List[TransactionResponse])
async def get_all_user_transactions(
        current_user: Annotated[User, Depends(UserService().get_current_user)]
) -> List[TransactionResponse]:
    transactions = await TransactionService().get_all_user_transactions(current_user)
    return list(map(lambda x: TransactionResponse(**x.to_dict()), transactions))


# await UserService().update_user_plan(transaction.user_id, transaction.plan)


@router.post("/new_payment", response_model=TransactionURLResponse)
async def new_payment(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        plan: Plans
):
    return TransactionURLResponse(url=await TransactionService().create_transaction(current_user, plan))


@router.get("/is_confirmed/{idempotency_key}    ", response_model=CheckConfirmedResponse)
async def check_transaction_confirmed(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        idempotency_key: uuid.UUID
) -> CheckConfirmedResponse:
    return CheckConfirmedResponse(is_confirmed=await TransactionService().check_confirm(current_user, idempotency_key))
