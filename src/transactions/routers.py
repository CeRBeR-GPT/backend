import uuid

from fastapi import APIRouter, Depends, Request
from typing import Annotated, List

from src.transactions.schemas import TransactionResponse, TransactionURLResponse, CheckConfirmedResponse, PlanResponse
from src.transactions.services import TransactionService

from src.users.models import User, Plans
from src.users.schemas import UserResponse
from src.users.services import UserService

router = APIRouter(tags=["transaction"], prefix="/transaction")


@router.get("/plans", response_model=List[PlanResponse])
async def get_all_plans() -> List[PlanResponse]:
    return await TransactionService().get_plans_list()


@router.get("/all", response_model=List[TransactionResponse])
async def get_all_user_transactions(
        current_user: Annotated[User, Depends(UserService().get_current_user)]
) -> List[TransactionResponse]:
    transactions = await TransactionService().get_all_user_transactions(current_user)
    return list(map(lambda x: TransactionResponse(**x.to_dict()), transactions))


@router.post("/new_payment", response_model=TransactionURLResponse)
async def new_payment(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        plan: Plans
):
    return TransactionURLResponse(url=await TransactionService().create_transaction(current_user, plan))


@router.post("/notifications", response_model=UserResponse)
async def payment_confirm(request: Request) -> UserResponse:
    req_json = await request.json()
    print(req_json)

    if req_json["event"] == "payment.succeeded":
        payment_id = req_json["object"]["id"]

        transaction = await TransactionService().confirm_payment(payment_id)
        user = await UserService().update_user_plan(transaction.user_id, transaction.plan)

        return UserResponse(**user.to_dict())


@router.get("/is_confirmed/{idempotency_key}    ", response_model=CheckConfirmedResponse)
async def check_transaction_confirmed(
        current_user: Annotated[User, Depends(UserService().get_current_user)],
        idempotency_key: uuid.UUID
) -> CheckConfirmedResponse:
    return CheckConfirmedResponse(is_confirmed=await TransactionService().check_confirm(current_user, idempotency_key))
