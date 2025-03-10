import datetime

from enum import Enum
from typing import Dict, Any
import uuid

from sqlalchemy import UUID, func, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    password_hash: Mapped[bytes] = mapped_column()
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "email": self.email,
            "is_admin": self.is_admin,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


class VerifyCode(Base):
    __tablename__ = "verify_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(50), unique=True)
    code: Mapped[int] = mapped_column()
