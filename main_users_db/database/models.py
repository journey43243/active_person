from sqlalchemy.dialects.postgresql import ENUM
from enum import Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import UUID, String, Integer
from uuid import uuid4
from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber


class Base(DeclarativeBase):
    pass


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
