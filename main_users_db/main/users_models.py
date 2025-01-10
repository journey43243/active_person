from pydantic import BaseModel, EmailStr, field_validator
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from passlib.context import CryptContext
import string
import asyncio


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegistrationValidation(BaseModel):

    username: str
    password: str
    email: EmailStr
    number: PhoneNumber
    age: Optional[int]

    async def set_hash_password(self):
        self.password = pwd_context.hash(self.password)

    async def set_phone_number(self):
        self.number = self.number[4:]
        print('here')

    @field_validator('username')
    @classmethod
    def username_validation(cls, username):
        if len(username) > 32:
            raise ValueError('Username must contains less than 32 characters')
        if len(username) < 8:
            raise ValueError('Username must contains more than 8 characters')
        return username

    @field_validator('password')
    @classmethod
    def password_validation(cls, password):
        if len(password) < 8:
            raise ValueError('Password must contains more than 8 characters')
        if len(password) > 32:
            raise ValueError('Password must contains less than 32 characters')
        if not any((i in password) for i in '0123456789'):
            raise ValueError('Password must contains numbers')
        if not any((i in password) for i in string.ascii_uppercase):
            raise ValueError('Password must contains capital letters')
        return password

    @field_validator('age')
    @classmethod
    def age_validator(cls, age):
        if age <= 0:
            raise ValueError('Your age should be more than zero')
        if age >= 75:
            raise ValueError('Error')
        return age


class AuthenticationValidation(BaseModel):
    login: str
    password: str


class UserGetResponse(BaseModel):
    username: str
    email: EmailStr
    number: PhoneNumber
    age: Optional[int]
    is_active: int
    is_superuser: int


class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    number: Optional[PhoneNumber] = None
    age: Optional[int] = None
    is_active: Optional[int] = None
