import asyncio
import uuid

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.transactions.schemas import AvailableProviders
from statistic.schemas import UserDocument
from statistic.utils import get_or_create_user


async def init_mongo():
    client = AsyncIOMotorClient("mongodb://localhost:27017/ai-chat")
    await init_beanie(
        database=client.ai_chat,
        document_models=[UserDocument]
    )


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
        )

        for provider, count in user_data["messages"]:
            await user.add_message(provider, count)

        print(f"\nСтатистика пользователя ({user.user_id}):")
        for day_stat in user.statistics:
            print(f"\nДата: {day_stat.day}")
            for provider in day_stat.providers:
                print(f"  {provider.provider_name.value}:")
                print(f"    Сообщений: {provider.messages_sent}")
                print(f"    Последняя активность: {provider.last_activity}")

        print("\n" + "=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
