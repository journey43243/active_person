from pydantic import BaseModel, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegistrationValidation(BaseModel):
    username: str
    password: str
    email: EmailStr
    phone_number: PhoneNumber
    age: Optional[int]

    async def set_hash_password(self):
        self.password = pwd_context.hash(self.password)

    async def set_phone_number(self):
        self.phone_number = self.phone_number[6:]

class AuthenticationValidation(BaseModel):
    login: str
    password: str
