import uuid
from typing import List

from yookassa import Payment, Configuration
from yookassa.domain.response import PaymentResponse

from src.transactions.exceptions import TransactionNotFoundException, FreePlanException, WeakerPlanException
from src.transactions.models import Transaction
from src.transactions.repositories import TransactionRepository

from src.users.models import Plans, plan_settings, User
from config_data.config import Config, load_config

settings: Config = load_config(".env")
yookassaData = settings.yookassaData

Configuration.account_id = yookassaData.CLIENT_ID
Configuration.secret_key = yookassaData.CLIENT_SECRET


class TransactionService:
    repository = TransactionRepository()

    @staticmethod
    def create_yookassa_transaction(
            idempotency_key: uuid.UUID, amount: float, description: str, return_url: str
    ) -> PaymentResponse:
        payment = Payment.create(
            {
                "amount": {"value": amount, "currency": "RUB"},
                "confirmation": {"type": "redirect", "return_url": return_url},
                "capture": True,
                "description": description,
            },
            str(idempotency_key),
        )

        return payment

    async def create_transaction(self, user: User, plan: Plans) -> str:
        new_plan_about = plan_settings[plan.value]
        current_plan_about = plan_settings[user.plan.value]

        if new_plan_about["price"] <= 0:
            raise FreePlanException()

        if current_plan_about["price"] - new_plan_about["price"] >= 0:
            raise WeakerPlanException()

        amount = new_plan_about["price"]
        idempotency_key = uuid.uuid4()
        return_url = settings.variablesData.FRONTEND_HOST
        transaction = self.create_yookassa_transaction(
            idempotency_key,
            amount,
            new_plan_about["description"],
            return_url
        )

        transaction_id = transaction.id
        confirmation_url = transaction.confirmation.confirmation_url

        await self.repository.create_transaction(transaction_id, user.id, idempotency_key, plan, amount)

        return confirmation_url

    async def check_confirm(self, user: User, idempotency_key: uuid.UUID) -> bool:
        transaction = await self.repository.get_transaction_by_idempotency_key(idempotency_key)
        if transaction is None or transaction.user_id != user.id:
            raise TransactionNotFoundException()

        return transaction.is_confirmed

    async def confirm_payment(self, transaction_id: str) -> Transaction:
        return await self.repository.confirm_transaction(transaction_id)

    async def get_all_user_transactions(self, user: User) -> List[Transaction]:
        return await self.repository.get_all_user_transaction(user.id)
