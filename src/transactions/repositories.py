import datetime
import uuid
from typing import List

from sqlalchemy import insert, select, update

from src.database import async_session
from src.transactions.models import Transaction
from src.users.models import Plans


class TransactionRepository:
    async def create_transaction(
            self,
            transaction_id: str,
            user_id: uuid.UUID,
            idempotency_key: uuid.UUID,
            plan: Plans,
            plan_expire_date: datetime.date,
            amount: float
    ) -> Transaction:
        async with async_session() as session:
            stmt = insert(Transaction).values(
                id=transaction_id,
                idempotency_key=idempotency_key,
                user_id=user_id,
                plan=plan,
                plan_expire_date=plan_expire_date,
                amount=amount
            )
            await session.execute(stmt)
            await session.commit()

        return await self.get_transaction_by_id(transaction_id)

    async def get_transaction_by_id(self, transaction_id: str) -> Transaction:
        async with async_session() as session:
            query = select(Transaction).where(Transaction.id == transaction_id)
            result = await session.execute(query)
            transaction = result.scalars().first()

        return transaction

    async def get_all_user_transaction(self, user_id: uuid.UUID) -> List[Transaction]:
        async with async_session() as session:
            query = select(Transaction).where(Transaction.user_id == user_id)
            result = await session.execute(query)
            transactions = result.scalars().all()

        return transactions

    async def get_transaction_by_idempotency_key(self, idempotency_key: uuid.UUID) -> Transaction:
        async with async_session() as session:
            query = select(Transaction).where(Transaction.idempotency_key == idempotency_key)
            result = await session.execute(query)
            transaction = result.scalars().first()

        return transaction

    async def confirm_transaction(self, transaction_id: str) -> Transaction:
        async with async_session() as session:
            stmt = update(Transaction).where(Transaction.id == transaction_id).values(is_confirmed=True)
            await session.execute(stmt)
            await session.commit()

        return await self.get_transaction_by_id(transaction_id)
