import uuid

from yookassa import Payment, Configuration
from yookassa.domain.response import PaymentResponse

from src.transactions.exceptions import TransactionNotFoundException
from src.transactions.models import Transaction
from src.transactions.repositories import TransactionRepository

from src.users.models import PlansPayment, plan_settings, User

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

    async def create_transaction(self, user: User, plan: PlansPayment) -> str:
        new_plan = plan.value

        amount = plan_settings[new_plan]["price"]
        idempotency_key = uuid.uuid4()
        return_url = f"{settings.variablesData.BASE_URL}/payment/{idempotency_key}"
        payment = self.create_yookassa_transaction(
            idempotency_key,
            amount,
            new_plan["description"],
            return_url
        )

        payment_id = payment.id
        confirmation_url = payment.confirmation.confirmation_url

        await self.repository.create_transaction(payment_id, user.id, idempotency_key, amount)

        return confirmation_url

    async def check_confirm(self, idempotency_key: uuid.UUID) -> bool:
        transaction = await self.repository.get_transaction_by_idempotency_key(idempotency_key)
        if transaction is None:
            raise TransactionNotFoundException()

        return transaction.is_confirmed

    async def confirm_payment(self, transaction_id: str) -> Transaction:
        return await self.repository.confirm_transaction(transaction_id)
