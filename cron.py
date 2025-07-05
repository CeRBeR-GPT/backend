import asyncio

from src.users.repositories import UserRepository
from src.logger import logger


async def daily_users_update(repo: UserRepository):
    await repo.reset_available_messages()
    await repo.reset_users_plan_to_default()
    await repo.delete_old_default_users_messages()

    logger.info("Successful daily update!")


user_repository = UserRepository()

if __name__ == "__main__":
    asyncio.run(daily_users_update(user_repository))
