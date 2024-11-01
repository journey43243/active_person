import pytest
from logger.logger import Logger
from conftest import TestPostgresDatabase
from main_users_db.database.users_orm import UsersOrm
from main_users_db.database.models import PhoneNumber, UserValidationReg, UserValidationAuth

testdb = TestPostgresDatabase()
logs = Logger(__name__).get_logger()


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize('user, excepted_value', [
    (UserValidationReg(name='string', age=0,
                       number=PhoneNumber('+79114445566'),
                       email='user1@test.com',
                       password='string'), 'string'),
    (UserValidationReg(name='string1', age=0,
                       number=PhoneNumber('+79124445566'),
                       email='user2@test.com',
                       password='string'), 'string1'),
    (UserValidationReg(name='string2', age=0,
                       number=PhoneNumber('+79134445566'),
                       email='user3@test.com',
                       password='string'), 'string2')
])
async def test_create_user_and_get_user(user, excepted_value):
    await user.set_hash_password()
    await user.set_number()
    await UsersOrm.create_user(user, testdb)
    name = await UsersOrm.get_user(user.name, testdb)
    assert name.username == excepted_value


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize('user, excepted_value', [
    (UserValidationAuth(login='string', password='string'), True),
    (UserValidationAuth(login='user1@test.com', password='string'), True),
    (UserValidationAuth(login='udfgdgdfgdgdfgdfr@example.com', password='string'), False)

])
async def test_authenticate_user(user, excepted_value):
    result = await UsersOrm.authenticate_user(user, testdb)
    assert result[0] if type(result) == tuple else result == excepted_value

