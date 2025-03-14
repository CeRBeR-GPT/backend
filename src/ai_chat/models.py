import datetime
import uuid
from enum import Enum

from sqlalchemy import UUID, func, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any, List

from src.database import Base


class MessageBelong(Enum):
    user_message = "user"
    assistant_message = "assistant"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(String(100000))
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    message_belong: Mapped[MessageBelong] = mapped_column(default=MessageBelong.user_message)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    chat: Mapped["Chat"] = relationship(back_populates="messages", uselist=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "message_belong": self.message_belong.value,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "created_at": self.created_at
        }


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    messages: Mapped[List["Message"]] = relationship(back_populates="chat", uselist=True,
                                                     lazy="selectin", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "messages": [message.to_dict() for message in self.messages],
        }
