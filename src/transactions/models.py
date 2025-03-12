import datetime
import uuid

from sqlalchemy import UUID, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any

from src.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(primary_key=True)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount: Mapped[str] = mapped_column()
    is_confirmed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    user: Mapped["User"] = relationship(back_populates="transactions", uselist=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "is_confirmed": self.is_confirmed,
            "created_at": self.created_at
        }
