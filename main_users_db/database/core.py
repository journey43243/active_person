from typing import AsyncGenerator
from .config import settings
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from redis.asyncio import Redis
from redis import Redis as syncRedis
import os
from dotenv import load_dotenv
from main.patterns.singleton import Singleton
from enum import Enum

load_dotenv()


class PostgresDatabase(metaclass=Singleton):

    def __init__(self):
        self.engine = create_async_engine(
            url=settings.DATABASE_URL_asyncpg,
            echo=True,
            pool_size=5,
            max_overflow=15
        )
        self.session_factory = async_sessionmaker(self.engine,
                                                  class_=AsyncSession,
                                                  expire_on_commit=False)
        self.metadata = MetaData()

    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        yield self.session_factory


class RedisDatabaseEnum(Enum):
    token_base = 0
    login_tree_base = 1


class RedisDatabase:

    def __init__(self, db):
        self.async_client = Redis(
            host=f'{os.environ.get("REDIS_HOST")}', port=int(os.environ.get("REDIS_PORT")),
            db=db, username=str(os.environ.get("REDIS_USER")),
            password=str(os.environ.get("REDIS_USER_PASSWORD")))

        self.sync_client = syncRedis(
            host=f'{os.environ.get("REDIS_HOST")}', port=int(os.environ.get("REDIS_PORT")),
            db=db, username=str(os.environ.get("REDIS_USER")),
            password=str(os.environ.get("REDIS_USER_PASSWORD")))

    async def get_async_client(self) -> AsyncGenerator[Redis, None]:
        yield self.async_client




