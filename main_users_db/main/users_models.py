from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
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
