import pytest
from main.users_models import RegistrationValidation
from conftest import get_async_client
from pydantic_extra_types.phone_numbers import PhoneNumber
import asyncio

@pytest.mark.parametrize('username, password, email, number, age', [
    ('user1sdfdsf', 'S1tringdfg', 'user1@example.com', "+79112223344", 14),
    ('userdfgdfgdf', 'S2string', 'user2@example.com', "+79112223345", 15),
    ('usdfsdfsdf', 'S3trinfdgdg', 'user3@example.com', "+79112223346", 4),
    ('dfgdgDFGdg3', 'sS3dfgdgg', 'udfgdfgd@example.com', "+79132223346", 5),
    ('df324DFG2343', 'stS3dgdfgdfgdgg', 'ud23423423gd@example.com', "+79132423346", 5)
])
async def test_registration_handler_positive(username, password, email, number, age,
                                             get_async_client: get_async_client):
    request = {"username": username,
               "password": password,
               "email": email,
               "number": PhoneNumber(number),
               "age": age}
    response = await get_async_client.post("/users/registration/", json=request)
    response_data = response.json()
    assert response_data["username"] == username
    assert response_data["email"] == email
    assert response_data["number"].replace('-', '')[4:] == number  # In model using type, which add tel: to start number
    assert response_data["age"] == age
    assert response_data["is_active"] == 1
    assert response_data["is_superuser"] == 0
    assert response.status_code == 201


@pytest.mark.parametrize('username, password, email, number, age', [
    ('user1', 'S1tringdfg', 'user1@example.com', "+79112223344", 14),
    ('user1sdfdsf', 'S1tring', 'user1@example.com', "+79112223344", 14),
    ('user1sdfdsfsdfsdfsdfsdfsdfsdfsdfsdfsd', 'S1tringdfg', 'user1@example.com', "+79112223344", 14),
    ('user1sdfdsf', 'S1tringdfgdfgdfgdfgdgdfgdfgdgdfgdgdfdfg', 'user1@example.com', "+79112223344", 14),
    ('user1sdfdsf', 's1tringdfg', 'user1@example.com', "+79112223344", 14),
    ('user1sdfdsf', 'Sgtringdfg', 'user1@example.com', "+79112223344", 14),
    ('user1sdfdsf', 'S1tringdfg', 'user1example.com', "+79112223344", 14),
    ('user1sdfdsf', 'S1tringdfg', 'user1@example.com', "+79112223344", 0),
    ('user1sdfdsf', 'S1tringdfg', 'user1@example.com', "+79112223344", -14),
    ('user1sdfdsf', 'S1tringdfg', 'user1@example.com', "+79112223344", 79),
])
async def test_registration_handler_validation_negative(username, password, email, number, age,
                                             get_async_client: get_async_client):
    request = {"username": username,
               "password": password,
               "email": email,
               "number": PhoneNumber(number),
               "age": age}
    response = await get_async_client.post("/users/registration/", json=request)
    assert response.status_code == 422



@pytest.mark.parametrize('username, password, email, number, age', [
    ('user1sdfdsf', 'S1tringdfg', 'user1@example.com', "+79112223344", 14),
    ('userdfgdfgdf', 'S2string', 'user2@example.com', "+79112223345", 15),
    ('usdfsdfsdf', 'S3trinfdgdg', 'user3@example.com', "+79112223346", 4),
    ('dfgdgDFGdg3', 'sS3dfgdgg', 'udfgdfgd@example.com', "+79132223346", 5),
    ('df324DFG2343', 'stS3dgdfgdfgdgg', 'ud23423423gd@example.com', "+79132423346", 5)
])
async def test_registration_handler_negative(username, password, email, number, age,
                                             get_async_client: get_async_client):
    request = {"username": username,
               "password": password,
               "email": email,
               "number": number,
               "age": age}
    unvalidResponse1 = await get_async_client.post("/users/registration/", json=request)
    assert unvalidResponse1.status_code == 422
    request["username"] += "t"
    unvalidResponse2 = await get_async_client.post("/users/registration/", json=request)
    assert unvalidResponse2.status_code == 422
    request["email"] += "1t"
    unvalidResponse3 = await get_async_client.post("/users/registration/", json=request)
    assert unvalidResponse3.status_code == 422
    request["number"] = request["number"].replace('1', '4')
    unvalidResponse4 = await get_async_client.post("/users/registration/", json=request)
    assert unvalidResponse4.status_code == 201