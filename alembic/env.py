import asyncio
import os
import sys

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

parent_dir = os.path.abspath(os.path.join(os.getcwd()))
sys.path.append(parent_dir)

from skaben.models.base import Base as app_base
from skaben.config import get_settings
from skaben.models import (
    device,
)

target_metadata = app_base.metadata
settings = get_settings()


def run_migrations_offline():
    context.configure(url=settings.asyncpg_url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_async_engine(settings.asyncpg_url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
