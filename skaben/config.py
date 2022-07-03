import os
from functools import lru_cache

from pydantic import BaseSettings

from skaben.utils import get_logger

logger = get_logger(__name__)


class AMQPSettings(BaseSettings):
    """AMQP settings"""

    user: str
    password: str
    host: str
    port: int = os.getenv('PORT', 5672)
    timeout: int = os.getenv('TIMEOUT', 10)
    limited: bool = os.getenv('LIMITED', False)

    class Config:
        env_prefix = "AMQP_"


class Settings(BaseSettings):
    """

    BaseSettings, from Pydantic, validates the data so that when we create an instance of Settings,
     environment and testing will have types of str and bool, respectively.

    Parameters:
    pg_user (str):
    pg_pass (str):
    pg_database: (str):
    pg_test_database: (str):
    asyncpg_url: AnyUrl:
    asyncpg_test_url: AnyUrl:

    Returns:
    instance of Settings

    """

    pg_host: str = os.getenv("DB_HOST")
    pg_user: str = os.getenv("POSTGRES_USER")
    pg_pass: str = os.getenv("POSTGRES_PASSWORD")
    pg_database: str = os.getenv("POSTGRES_DB")

    jwt_secret_key: str = os.getenv("SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("ALGORITHM", "")
    jwt_access_toke_expire_minutes: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1)

    amqp: AMQPSettings = AMQPSettings()

    amqp_uri: str = f'pyamqp://{amqp.user}:{amqp.password}@{amqp.host}:{amqp.port}'
    asyncpg_url: str = f"postgresql+asyncpg://{pg_user}:{pg_pass}@{pg_host}:5432/{pg_database}"


@lru_cache()
def get_settings():
    logger.info("Loading config settings from the environment...")
    settings = Settings()
    return settings
