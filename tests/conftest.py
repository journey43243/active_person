import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
import redis.asyncio as async_redis
from redis import Redis as sync_redis
from contextlib import asynccontextmanager
from pydantic_settings import BaseSettings, SettingsConfigDict
from dataclasses import dataclass
import os
from dotenv import get_key
import redis
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


@dataclass
class TestMixin:
    __env_path: str = os.path.join(os.path.dirname('active_person'), '.env')
    __key: str = get_key(__env_path, "SECRET_KEY_1")
    __ALGORITHM: str = "HS256"
    __expire_minutes_access: int = int(get_key(__env_path, 'ACCESS_TOKEN_EXPIRE_MINUTES'))
    __expire_minutes_refresh: int = int(get_key(__env_path, 'REFRESH_TOKEN_EXPIRE_MINUTES'))
    __redis_user: str = get_key(__env_path, 'TEST_REDIS_USER')
    __redis_pass: str = get_key(__env_path, 'TEST_REDIS_PASS')  # REFRESH_TOKEN_EXPIRE_MINUTES = 86400
    __redis_host: str = get_key(__env_path, "TEST_REDIS_HOST")
    __redis_port: str = get_key(__env_path, "TEST_REDIS_PORT")
    __redis_user_pass: str = get_key(__env_path, 'TEST_REDIS_USER_PASS')
    __sync_client: redis.Redis = sync_redis(
        host=f'{__redis_host}', port=int(__redis_port),
        db=0, username=__redis_user,
        password=__redis_pass)
    __async_client: redis.asyncio.Redis = async_redis.Redis(
        host=f'{__redis_host}', port=int(__redis_port),
        db=0, username=__redis_user,
        password=__redis_pass, decode_responses=True)
    __oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="token")
    __pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @property
    def redis_pass(self):
        return self.__redis_pass

    @property
    def redis_user(self):
        return self.__redis_user

    @property
    def redis_host(self):
        return self.__redis_host

    @property
    def redis_port(self):
        return self.__redis_port

    @property
    def secret_key(self):
        return self.__key

    @property
    def algorithm(self):
        return self.__ALGORITHM

    @property
    def exp_time_access(self):
        return self.__expire_minutes_access

    @property
    def pwd_context(self):
        return self.__pwd_context

    @property
    def exp_time_refresh(self):
        return self.__expire_minutes_refresh


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


class TestPostgresDatabase(TestMixin):

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

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        yield self.session_factory()


class TestRedisDatabase(TestMixin):

    def __init__(self):
        self.sync_client = sync_redis(
            host=f'{self.redis_host}', port=int(self.redis_port),
            db=0, username=str(self.redis_user),
            password=str(self.redis_pass))

        self.async_client = async_redis.Redis(
            host=f'{self.redis_host}', port=int(str(self.redis_port)),
            db=0, username=str(TestMixin().redis_user),
            password=str(self.redis_pass))

    @asynccontextmanager
    async def override_async_redis_client(self) -> AsyncGenerator[async_redis.Redis, None]:
        yield self.async_client


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
async def create_tables():
    db = TestPostgresDatabase()
    metadata = sa.MetaData()
    sa.Table('users',
             metadata,
             sa.Column('id', sa.UUID(), nullable=False),
             sa.Column('username', sa.String(length=32), nullable=False),
             sa.Column('age', sa.Integer(), nullable=False),
             sa.Column('number', sa.String(length=20), nullable=False),
             sa.Column('email', sa.String(), nullable=False),
             sa.Column('hashed_password', sa.String(), nullable=False),
             sa.Column('is_active', postgresql.ENUM('active', 'unactive', name='active_status_enum'), nullable=False),
             sa.Column('is_superuser', postgresql.ENUM('is_superuser', 'not_superuser', name='superuser_status_enum'),
                       nullable=False),
             sa.PrimaryKeyConstraint('id'),
             sa.UniqueConstraint('email'),
             sa.UniqueConstraint('number'),
             sa.UniqueConstraint('username')
             )

    async with db.engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    yield
    async with db.engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)





