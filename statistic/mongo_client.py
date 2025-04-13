import asyncio
import uuid

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field, BaseModel
from datetime import date, datetime
from typing import List, Optional

from src.transactions.schemas import AvailableProviders


class ProviderStatistic(BaseModel):
    provider_name: AvailableProviders
    messages_sent: int = 0
    last_activity: Optional[datetime] = None


class DayStatistic(BaseModel):
    day: date = Field(default_factory=date.today)
    providers: List[ProviderStatistic] = []

    def get_provider(self, provider_name: str) -> ProviderStatistic:
        for provider in self.providers:
            if provider.provider_name == provider_name:
                return provider

        new_provider = ProviderStatistic(provider_name=provider_name)
        self.providers.append(new_provider)
        return new_provider


class UserDocument(Document):
    user_id: uuid.UUID = Field(..., unique=True)
    username: Optional[str] = None
    statistics: List[DayStatistic] = []

    class Settings:
        name = "users"

    async def add_message(
            self,
            provider_name: str,
            count: int = 1,
            target_date: date = None
    ) -> None:
        target_date = target_date or date.today()

        day_stat = next(
            (s for s in self.statistics if s.day == target_date),
            None
        )

        if not day_stat:
            day_stat = DayStatistic(day=target_date)
            self.statistics.append(day_stat)

        provider = day_stat.get_provider(provider_name)
        provider.messages_sent += count
        provider.last_activity = datetime.now()

        await self.save()


async def init_mongo():
    client = AsyncIOMotorClient("mongodb://localhost:27017/ai-chat")
    await init_beanie(
        database=client.ai_chat,
        document_models=[UserDocument]
    )


async def get_or_create_user(user_id: uuid.UUID, username: str = None) -> UserDocument:
    user = await UserDocument.find_one(UserDocument.user_id == user_id)
    if not user:
        user = UserDocument(user_id=user_id, username=username)
        await user.save()
    elif username and not user.username:
        user.username = username
        await user.save()
    return user


async def main():
    await init_mongo()

    test_users = [
        {
            "id": "a8098c1a-f86e-11da-bd1a-00112444be1e",
            "name": "user1",
            "messages": [
                (AvailableProviders.DEEPSEEK, 5),
                (AvailableProviders.GPT_4O, 2)
            ]
        },
        {
            "id": "b9098d2b-f86e-11da-bd1a-00112444be2e",
            "name": "user2",
            "messages": [
                (AvailableProviders.DEFAULT, 3),
                (AvailableProviders.GPT_4, 4)
            ]
        },
        {
            "id": "c9098e3c-f86e-11da-bd1a-00112444be3e",
            "name": "user3",
            "messages": [
                (AvailableProviders.DEEPSEEK, 6),
                (AvailableProviders.DEFAULT, 1)
            ]
        },
        {
            "id": "d9098f4d-f86e-11da-bd1a-00112444be4e",
            "name": "user4",
            "messages": [
                (AvailableProviders.DEFAULT, 2),
                (AvailableProviders.DEEPSEEK, 3),
                (AvailableProviders.GPT_4O_MINI, 1)
            ]
        },
        {
            "id": "e9098f5e-f86e-11da-bd1a-00112444be5e",
            "name": "user5",
            "messages": [
                (AvailableProviders.GPT_4O_MINI, 7)
            ]
        }
    ]

    for user_data in test_users:
        user = await get_or_create_user(
            user_id=uuid.UUID(user_data["id"]),
            username=user_data["name"]
        )

        for provider, count in user_data["messages"]:
            await user.add_message(provider, count)

        print(f"\nСтатистика пользователя {user.username} ({user.user_id}):")
        for day_stat in user.statistics:
            print(f"\nДата: {day_stat.day}")
            for provider in day_stat.providers:
                print(f"  {provider.provider_name.value}:")
                print(f"    Сообщений: {provider.messages_sent}")
                print(f"    Последняя активность: {provider.last_activity}")

        print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
