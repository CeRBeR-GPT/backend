from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config_data.config import Config, load_config

database_config: Config = load_config(".env")
DATABASE_URL = database_config.database.DATABASE_URL

engine = create_async_engine(DATABASE_URL)
sync_engine = create_engine(DATABASE_URL)

async_session = async_sessionmaker(engine)
sync_session = sessionmaker(sync_engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass
