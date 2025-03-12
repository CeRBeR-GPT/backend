import uuid

from datetime import datetime
from pydantic import BaseModel

from src.users.models import Plans


class TransactionURLResponse(BaseModel):
    url: str


class CheckConfirmedResponse(BaseModel):
    is_confirmed: bool


class TransactionResponse(BaseModel):
    id: str
    user_id: uuid.UUID
    plan: Plans
    amount: float
    is_confirmed: bool
    created_at: datetime
