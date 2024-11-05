from typing import AsyncGenerator
from .config import settings
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
#from .models import Mixin
from contextlib import asynccontextmanager


class PostgresDatabase:

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

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        yield self.session_factory()

    async def get_metadata(self):
        return self.metadata


# class RedisDatabase(Mixin):
#
#     def __init__(self):
#         self.sync_client = sync_redis(
#             host=f'{Mixin.redis_host}', port=int(self.redis_port),
#             db=0, username=str(self.redis_user),
#             password=str(self.redis_pass))
#
#         self.async_client = async_redis.Redis(
#             host=f'{self.redis_host}', port=int(str(self.redis_port)),
#             db=0, username=str(Mixin().redis_user),
#             password=str(self.redis_pass))
#
#     @asynccontextmanager
#     async def get_sync_client(self) -> sync_redis:
#         yield self.sync_client
#
#     @asynccontextmanager
#     async def get_async_client(self) -> AsyncGenerator[async_redis.Redis, None]:
#         yield self.async_client



