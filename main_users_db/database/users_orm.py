from database.core import PostgresDatabase
from main.users_models import RegistrationValidation, AuthenticationValidation, pwd_context, UserGetResponse, UserUpdateRequest
from .models import Users
from sqlalchemy import select, func, delete, bindparam
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import asyncio


class UsersDDL:

    @classmethod
    async def create_user(cls, user: RegistrationValidation, session_depend) -> Users:
        try:
            async with session_depend() as session:

                us = Users(
                    username=user.username,
                    age=user.age,
                    number=user.number,
                    email=user.email,
                    hashed_password=user.password,
                )
                session.add(us)
                await session.commit()
                return us

        except IntegrityError as error:
            await session.rollback()

            if 'email' in error._message():
                raise HTTPException(status_code=422, detail=f'User with {user.email} already exists')

            if 'number' in error._message():
                raise HTTPException(status_code=422, detail=f'User with {user.number} already exists')

            if 'username' in error._message():
                raise HTTPException(status_code=422, detail=f'User with {user.username} already exists')

        finally:
            await session.close()

    @classmethod
    async def get_user(cls, name: str, session_depend) -> Users:
        async with session_depend() as session:

            select_by_username_exists_stmt = select(func.count()).select_from(Users).filter(Users.username == name)
            select_by_email_exists_stmt = select(func.count()).select_from(Users).filter(Users.email == name)

            first_stmt_result = await session.execute(select_by_username_exists_stmt)
            second_stmt_result = await session.execute(select_by_email_exists_stmt)

            if first_stmt_result.scalar_one():
                get_user_stmt = select(Users).filter(Users.username == name)
                user = await session.execute(get_user_stmt)

            elif second_stmt_result.scalar_one():
                get_user_stmt = select(Users).filter(Users.email == name)
                user = await session.execute(get_user_stmt)

            else:
                await session.close()
                raise HTTPException(status_code=404, detail="User not found")

            await session.close()
            return user.scalar_one()

    @classmethod
    async def update_user(cls, username: str, data, session_depend):
        user = await UsersDDL.get_user(username, session_depend)
        async with session_depend() as session:
            for attr, value in data.items():
                if value and attr != 'is_superuser':
                    setattr(user, attr, value)
            session.add(user)
            await session.commit()
            await session.close()

    @classmethod
    async def delete_user(cls, login, session_depend):
        async with session_depend() as session:
            delete_stmt = delete(Users).where(Users.username == login, Users.email == login)
            await session.execute(delete_stmt)
            await session.commit()
            await session.close()
