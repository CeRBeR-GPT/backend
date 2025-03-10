import asyncio
import os
import sys

from logging.config import fileConfig

from sqlalchemy.engine import Connection
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.database import Base

from src.users.models import User, VerifyCode  # noqa

from alembic import context

from config_data.config import Config, load_config

database_config: Config = load_config(".env")
DATABASE_URL = database_config.database.DATABASE_URL

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

sys.path.append(os.path.join(sys.path[0], "src"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
