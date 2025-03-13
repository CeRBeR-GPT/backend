import uuid

from datetime import datetime
from typing import Annotated, List
from pydantic import BaseModel, Field


class UserMessageResponse(BaseModel):
    id: uuid.UUID
    text: Annotated[str, Field(min_length=1, max_length=100000)]
    chat_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class AssistantMessageResponse(BaseModel):
    id: uuid.UUID
    text: str
    chat_id: uuid.UUID
    created_at: datetime


class AIChatResponse(BaseModel):
    id: uuid.UUID
    name: str
    user_id: uuid.UUID
    created_at: datetime
    user_messages: List[UserMessageResponse]
    assistant_messages: List[AssistantMessageResponse]
