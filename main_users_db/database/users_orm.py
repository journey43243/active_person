from main_users_db.database.core import PostgresDatabase, RedisDatabase
from main_users_db.database.models import Users, UserValidationReg, UserValidationAuth, Mixin
from sqlalchemy import select

pgdb = PostgresDatabase()
rdb = RedisDatabase()


class UsersOrm:

    @staticmethod
    async def create_user(user: UserValidationReg, db):
        async with db.get_async_session() as session:
            us = Users(
                username=user.name,
                age=user.age,
                number=user.number,
                email=user.email,
                hashed_password=user.password,
            )
            session.add(us)
            await session.commit()
            await session.close()

    @staticmethod
    async def get_user(name: str, db):
        stmt = select(Users).filter(Users.username == name)
        async with db.get_async_session() as session:
            user = await session.execute(stmt)
            await session.close()
            return user.first()[0]

    @staticmethod
    async def authenticate_user(plain_user: UserValidationAuth, db):
        login = plain_user.login
        password = plain_user.password
        async with db.get_async_session() as session:
            username_stmt = await session.execute(select(Users).where(Users.username == login))
            email_stmt = await session.execute(select(Users).where(Users.email == login))
            try:
                user = username_stmt.first()[0]
                return Mixin().pwd_context.verify(password, user.hashed_password), user.username
            except TypeError:
                print('here')
            finally:
                await session.close()
            try:
                user = email_stmt.first()[0]
                return Mixin().pwd_context.verify(password, user.hashed_password), user.username
            except TypeError:
                pass
            finally:
                await session.close()
            return False

