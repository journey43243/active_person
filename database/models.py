import dataclasses
import datetime

from pydantic_core import core_schema
from sqlalchemy.dialects.postgresql import ENUM
from enum import Enum
import redis
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import UUID, String, Integer
from uuid import uuid4
import os
from dotenv import get_key
import redis.asyncio as async_redis
from redis import Redis as sync_redis
from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from dataclasses import dataclass


class Base(DeclarativeBase):
    pass


@dataclass
class Mixin:

    __env_path: str = os.path.join(os.path.dirname('active_person'), '.env')
    __key: str = get_key(__env_path, "SECRET_KEY_1")
    __ALGORITHM: str = "HS256"
    __expire_minutes_access: int = int(get_key(__env_path, 'ACCESS_TOKEN_EXPIRE_MINUTES'))
    __expire_minutes_refresh: int = int(get_key(__env_path, 'REFRESH_TOKEN_EXPIRE_MINUTES'))
    __redis_user: str = get_key(__env_path, 'REDIS_USER')
    __redis_pass: str = get_key(__env_path, 'REDIS_PASS')#REFRESH_TOKEN_EXPIRE_MINUTES = 86400
    __redis_host: str = get_key(__env_path, "REDIS_HOST")
    __redis_port: str = get_key(__env_path, "REDIS_PORT")
    __redis_user_pass: str = get_key(__env_path, 'REDIS_USER_PASS')
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


# class CustomPhoneNumber(PhoneNumber):
#     def __init__(self):
#         super().__init__()
#
#     def _validate(cls, phone_number: str, _: core_schema.ValidationInfo) -> str:

class UserValidationReg(BaseModel, Mixin):

    name: str
    age: int
    number: PhoneNumber
    email: EmailStr
    password: str

    async def set_hash_password(self):
        self.password = self.pwd_context.hash(self.password)

    async def set_number(self) -> None:
        self.number = (self.number)[4:]


class UserValidationAuth(BaseModel):
    login: str
    password: str


class ActiveStatus(Enum):
    active = 1
    unactive = 0


class IsSuperUserStatus(Enum):
    is_superuser = 1
    not_superuser = 0


class Users(Base):

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID, default=uuid4, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    age: Mapped[int] = mapped_column(Integer)
    number: Mapped[PhoneNumber] = mapped_column(String(20), unique=True)
    email: Mapped[EmailStr] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[int] = mapped_column(ENUM(ActiveStatus, name="active_status_enum", create_type=False),
                                           default=ActiveStatus.active)
    is_superuser: Mapped[int] = mapped_column(ENUM(IsSuperUserStatus, name="superuser_status_enum", create_type=False),
                                              default=IsSuperUserStatus.not_superuser.not_superuser)
