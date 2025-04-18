from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from config_data.config import Config, load_config
from statistic.schemas import UserDocument

config: Config = load_config()
mongo_settings = config.mongoDB


async def init_mongo():
    if config.variablesData.MODE == "PROD":
        client = AsyncIOMotorClient(mongo_settings.MONGO_URL)
    else:
        client = AsyncIOMotorClient(mongo_settings.MONGO_LOCAL_URL)
    await init_beanie(
        database=client.ai_chat,
        document_models=[UserDocument]
    )
