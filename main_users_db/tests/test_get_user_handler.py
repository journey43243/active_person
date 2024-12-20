import pytest
from main.users_models import RegistrationValidation
from conftest import get_async_client
from pydantic_extra_types.phone_numbers import PhoneNumber
import asyncio

@pytest.mark.parametrize('login', [
    ('user1sdfdsf'),
    ('userdfgdfgdf'),
    ('usdfsdfsdf'),
    ('dfgdgDFGdg3'),
    ('df324DFG2343')
])
async def test_registration_handler_positive(login, get_async_client: get_async_client):
    request = {"login": login}
    response = await get_async_client.get(f"/users/get_user/?login={login}")
    response_data = response.json()
    # assert response_data["username"] == login
    # assert response_data["email"] == email
    # assert response_data["number"].replace('-', '')[4:] == number  # In model using type, which add tel: to start number
    # assert response_data["age"] == age
    # assert response_data["is_active"] == 1
    # assert response_data["is_superuser"] == 0
    assert response.status_code == 200