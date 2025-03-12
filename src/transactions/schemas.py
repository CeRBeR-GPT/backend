import uuid

from datetime import datetime
from pydantic import BaseModel


class TransactionResponse(BaseModel):
    id: uuid.UUID
    user_id: int
    amount: float
    is_confirmed: bool
    created_at: datetime
