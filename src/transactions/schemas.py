import uuid

from datetime import datetime
from typing import Literal
from pydantic import BaseModel

from src.users.models import Plans


class PlanResponse(BaseModel):
    name: str
    max_length: int
    count_limit: int
    price: int
    priority: Literal[1, 2, 3]


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
