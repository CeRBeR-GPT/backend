import uuid

from datetime import datetime
from typing import Annotated, List
from pydantic import BaseModel, Field

from src.ai_chat.models import MessageBelong


class MessageResponse(BaseModel):
    id: uuid.UUID
    text: str
    message_belong: MessageBelong
    chat_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class AIChatResponse(BaseModel):
    id: uuid.UUID
    name: str
    user_id: uuid.UUID
    created_at: datetime
    messages: List[MessageResponse]
