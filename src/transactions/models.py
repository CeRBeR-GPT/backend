import datetime
import uuid

from sqlalchemy import UUID, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from typing import Dict, Any

from src.database import Base
from src.users.models import Plans


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(primary_key=True)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan: Mapped[Plans] = mapped_column()
    amount: Mapped[float] = mapped_column()
    is_confirmed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan": self.plan.value,
            "amount": self.amount,
            "is_confirmed": self.is_confirmed,
            "created_at": self.created_at
        }
