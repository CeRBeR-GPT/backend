import uuid

from datetime import datetime
from enum import Enum
from typing import Literal, List
from pydantic import BaseModel

from src.users.models import Plans


class AvailableProviders(str, Enum):
    DEFAULT = "default"
    DEEPSEEK = "deepseek"
    GPT_4O_MINI = "gpt_4o_mini"
    GPT_4O = "gpt_4o"
    GPT_4 = "gpt_4"


class PlanResponse(BaseModel):
    name: str
    max_length: int
    count_limit: int
    chats_limit: int
    price: int
    priority: Literal[1, 2, 3]
    available_providers: List[AvailableProviders]


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
