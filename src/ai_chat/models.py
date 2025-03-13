import datetime
import uuid

from sqlalchemy import UUID, func, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any, List

from src.database import Base


class UserMessage(Base):
    __tablename__ = "user_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(String(100000))
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    chat: Mapped["Chat"] = relationship(back_populates="user_messages", uselist=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "created_at": self.created_at
        }


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(String(100000))
    chat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    chat: Mapped["Chat"] = relationship(back_populates="assistant_messages", uselist=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "chat_id": self.chat_id,
            "created_at": self.created_at
        }


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    user_messages: Mapped[List["UserMessage"]] = relationship(back_populates="chat", uselist=True,
                                                              lazy="selectin", cascade="all, delete-orphan")
    assistant_messages: Mapped[List["AssistantMessage"]] = relationship(back_populates="chat", uselist=True,
                                                                        lazy="selectin", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "user_messages": [message.to_dict() for message in self.user_messages],
            "assistant_messages": [message.to_dict() for message in self.assistant_messages]
        }
