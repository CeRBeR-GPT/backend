from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from config_data.config import Config, load_config

database_config: Config = load_config(".env")
DATABASE_URL = database_config.database.DATABASE_URL

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass
