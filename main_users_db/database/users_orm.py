from database.core import PostgresDatabase
from models.users_models import RegistrationValidation, AuthenticationValidation, pwd_context
from .models import Users
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

pgdb = PostgresDatabase()


class UsersOrm:

    @staticmethod
    async def create_user(user: RegistrationValidation, db):
        #try:
            async with db.get_async_session() as session:
                us = Users(
                    username=user.username,
                    age=user.age,
                    number=user.number,
                    email=user.email,
                    hashed_password=user.password,
                )
                session.add(us)
                await session.commit()
                await session.close()
        #except IntegrityError:


    @staticmethod
    async def get_user(name: str, db):
        try:
            stmt = select(Users).filter(Users.username == name)
            async with db.get_async_session() as session:
                user = await session.execute(stmt)
                await session.close()
                return user.first()[0]
        except TypeError:
            try:
                stmt = select(Users).filter(Users.email == name)
                async with db.get_async_session() as session:
                    user = await session.execute(stmt)
                    await session.close()
                    return user.first()[0]
            except TypeError:
                return False

    @staticmethod
    async def authenticate_user(plain_user: AuthenticationValidation, db):
        login = plain_user.login
        password = plain_user.password
        async with db.get_async_session() as session:
            username_stmt = await session.execute(select(Users).where(Users.username == login))
            email_stmt = await session.execute(select(Users).where(Users.email == login))
            try:
                user = username_stmt.first()[0]
                return pwd_context.verify(password, user.hashed_password), user.username
            except TypeError:
                pass
            finally:
                await session.close()
            try:
                user = email_stmt.first()[0]
                return pwd_context.verify(password, user.hashed_password), user.username
            except TypeError:
                pass
            finally:
                await session.close()
            return False

