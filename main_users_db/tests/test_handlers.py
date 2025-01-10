import pytest
from main.users_models import RegistrationValidation
from conftest import async_client
from pydantic_extra_types.phone_numbers import PhoneNumber
import asyncio


@pytest.mark.parametrize('username, password, email, number, age', [
    ('user1sdfdsf', 'S1tringdfg', 'user1@example.com', "+79112223344", 14),
    ('userdfgdfgdf', 'S2string', 'user2@example.com', "+79112223345", 15),
    ('usdfsdfsdf', 'S3trinfdgdg', 'user3@example.com', "+79112223346", 4),
    ('dfgdgDFGdg3', 'sS3dfgdgg', 'udfgdfgd@example.com', "+79132223346", 5),
    ('df324DFG2343', 'stS3dgdfgdfgdgg', 'ud23423423gd@example.com', "+79132423346", 5)
])
async def test_registration_and_get_user_handlers_positive(username, password, email, number, age,
                                                           async_client):
    request = {"username": username,
               "password": password,
               "email": email,
               "number": PhoneNumber(number),
               "age": age}
    response = await async_client.post("/users/registration/", json=request)
    get_response_by_username, get_response_by_email = await asyncio.gather(
        async_client.get(f"/users/get_user/?login={username}"),
        async_client.get(f"/users/get_user/?login={email}")
    )
    response_data = response.json()
    print(response_data)
    assert response_data["username"] == username
    assert response_data["email"] == email
    assert response_data["number"].replace('-', '')[4:] == number  # In model using type, which add tel: to start number
    assert response_data["age"] == age
    assert response_data["is_active"] == 1
    assert response_data["is_superuser"] == 0
    assert response.status_code == 201
    assert get_response_by_username.status_code == 200
    assert get_response_by_email.status_code == 200


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
                                                        async_client: async_client):
    request = {"username": username,
               "password": password,
               "email": email,
               "number": PhoneNumber(number),
               "age": age}
    response = await async_client.post("/users/registration/", json=request)
    print(response.json())
    assert response.status_code == 422


@pytest.mark.parametrize('username, password, email, number, age', [
    ('user1sdfdsf', 'S1tringdfg', 'user1@example.com', "+79112223344", 14),
    ('userdfgdfgdf', 'S2string', 'user2@example.com', "+79112223345", 15),
    ('usdfsdfsdf', 'S3trinfdgdg', 'user3@example.com', "+79112223346", 4),
    ('dfgdgDFGdg3', 'sS3dfgdgg', 'udfgdfgd@example.com', "+79132223346", 5),
    ('df324DFG2343', 'stS3dgdfgdfgdgg', 'ud23423423gd@example.com', "+79132423346", 5)
])
async def test_registration_handler_negative(username, password, email, number, age,
                                             async_client: async_client):
    start_request = {"username": username,
                     "password": password,
                     "email": email,
                     "number": number,
                     "age": age}
    first_invalid_request = {"username": username + 't',
                             "password": password,
                             "email": email,
                             "number": number,
                             "age": age}
    second_invalid_request = {"username": username + 't',
                              "password": password,
                              "email": '1t' + email,
                              "number": number,
                              "age": age}
    valid_request = {"username": username + 't',
                     "password": password,
                     "email": '1t' + email,
                     "number": number.replace('1', '4'),
                     "age": age}
    unvalid_response1, unvalid_response2, unvalid_response3, valid_response = await asyncio.gather(
        async_client.post("/users/registration/", json=start_request),
        async_client.post("/users/registration/", json=first_invalid_request),
        async_client.post("/users/registration/", json=second_invalid_request),
        async_client.post("/users/registration/", json=valid_request))

    print(valid_response.json())
    # assert unvalid_response1.status_code == 422
    # assert unvalid_response2.status_code == 422
    # assert unvalid_response3.status_code == 422
    # assert valid_response.status_code == 201



@pytest.mark.parametrize('username, password, email', [
    ('user1sdfdsf', 'S1tringdfg', 'user1@example.com'),
    ('userdfgdfgdf', 'S2string', 'user2@example.com'),
    ('usdfsdfsdf', 'S3trinfdgdg', 'user3@example.com'),
    ('dfgdgDFGdg3', 'sS3dfgdgg', 'udfgdfgd@example.com'),
    ('df324DFG2343', 'stS3dgdfgdfgdgg', 'ud23423423gd@example.com')
])
async def test_authentication_and_current_user_positive(username, password, email, async_client):
    request_by_username = {
        "login": username,
        "password": password
    }
    request_by_email = {
        "login": email,
        "password": password
    }
    response_by_username, response_by_email = await asyncio.gather(
        async_client.post("/users/authentication/", json=request_by_username),
        async_client.post("/users/authentication/", json=request_by_email),
    )

    cookies = {"access_token": response_by_username.cookies.get("access_token")}
    cur_user_response = await async_client.get("/users/current_user/",cookies=cookies)
    print(cur_user_response.cookies)
    assert response_by_username.status_code == 200
    assert response_by_email.status_code == 200
    assert cur_user_response.status_code == 200
    assert cur_user_response.json() == username



@pytest.mark.parametrize('username, password, email', [
    ('user1sdfdsf', 'S1tringdfgdfgfd', 'user1@example.com'),
    ('userdfgdfgdf', 'S2stringdfgdf', 'user2@example.com'),
    ('usdfsdfsdf', 'S3trinfdgdgdfgdf', 'user3@example.com'),
    ('dfgdgDFGdg3', 'sS3dfgdggdfgdf', 'udfgdfgd@example.com'),
    ('df324DFG2343', 'stS3dgdfgdfgdggfdgdf', 'ud23423423gd@example.com')
])
async def test_authentication_negative(username, password, email, async_client):
    request_by_username = {
        "login": username,
        "password": password
    }
    request_by_email = {
        "login": email,
        "password": password
    }
    response_by_username, response_by_email = await asyncio.gather(
        async_client.post("/users/authentication/", json=request_by_username),
        async_client.post("/users/authentication/", json=request_by_email)
    )
    assert response_by_username.status_code == 401
    assert response_by_email.status_code == 401


@pytest.mark.parametrize('username, email', [
    ('user1sdfdsftdfgf', 'user1t@example.com'),
    ('userdfgdfgdftdfgdf','user2t@example.com'),
    ('usdfsdfsdfdfgdfgt', 'user3t@example.com'),
    ('dfgdgDFGddfgdfg3t','udfgdfgdt@example.com'),
    ('df324DFG234fdgdf3t','ud23423423gdt@example.com')
])
async def test_get_user_negative(username, email,async_client):
    response1, response2 = await asyncio.gather(
        async_client.get(f"/users/get_user/?login={username}"),
        async_client.get(f"/users/get_user/?login={email}")
        )
    assert response1.status_code == 404
    assert response2.status_code == 404

