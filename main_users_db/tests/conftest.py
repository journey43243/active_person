import pytest
from typing import AsyncGenerator
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from redis.asyncio import Redis
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import asyncio
from pydantic_settings import BaseSettings, SettingsConfigDict
from database.models import Base
from main.server import app
from database.core import PostgresDatabase, RedisDatabase
from httpx import ASGITransport, AsyncClient
import sqlalchemy as sa
from alembic import op
from sqlalchemy.pool import NullPool
from pydantic_extra_types.phone_numbers import PhoneNumber

load_dotenv()


class TestSettings(BaseSettings):
    TEST_DB_HOST: str
    TEST_DB_PORT: int
    TEST_DB_USER: str
    TEST_DB_PASS: str
    TEST_DB_NAME: str

    @property
    def DATABASE_URL_asyncpg(self):
        return f"postgresql+asyncpg://{self.TEST_DB_USER}:{self.TEST_DB_PASS}" + \
               f"@{self.TEST_DB_HOST}:{self.TEST_DB_PORT}/{self.TEST_DB_NAME}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = TestSettings()


class TestPostgresDatabase:

    def __init__(self):
        self.engine = create_async_engine(
            url=settings.DATABASE_URL_asyncpg,
            echo=True,
            poolclass=NullPool
        )
        self.session_factory = async_sessionmaker(self.engine,
                                                  class_=AsyncSession,
                                                  expire_on_commit=False)
        self.metadata = MetaData()

    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        yield self.session_factory


class TestRedisDatabase:

    def __init__(self):
        self.async_client = Redis(
            host=f'{os.environ.get("TEST_REDIS_HOST")}', port=int(os.environ.get("TEST_REDIS_PORT")),
            db=0, username=str(os.environ.get("TEST_REDIS_USER")),
            password=str(os.environ.get("TEST_REDIS_USER_PASSWORD")))

    async def get_async_client(self) -> AsyncGenerator[Redis, None]:
        yield self.async_client


db = PostgresDatabase()
cache = RedisDatabase()

testdb = TestPostgresDatabase()
testcache = TestRedisDatabase()

Base.metadata.bind = testdb.engine

app.dependency_overrides[db.get_async_session] = testdb.get_async_session
app.dependency_overrides[cache.get_async_client] = testcache.get_async_client


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with testdb.engine.begin() as conn:
        await conn.run_sync(sa.Enum('is_superuser', 'not_superuser', name='superuser_status_enum').create)
        await conn.run_sync(sa.Enum('active', 'unactive', name='active_status_enum').create)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with testdb.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(sa.Enum('is_superuser', 'not_superuser', name='superuser_status_enum').drop)
        await conn.run_sync(sa.Enum('active', 'unactive', name='active_status_enum').drop)


@pytest.fixture(scope="session")
async def get_async_client():
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as ac:
        yield ac

