from fastapi import FastAPI, APIRouter, Depends, Request
from uvicorn import run
from database.users_orm import UsersDDL, RegistrationValidation, AuthenticationValidation, pwd_context, UserGetResponse, \
    UserUpdateRequest
from database.core import PostgresDatabase
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi_utils.cbv import cbv
from .logger import Logger, logging
from .tokens import Token
import asyncio
from typing import AsyncGenerator, Union

from database.core import RedisDatabase
from database.models import Users

token = Token()

app = FastAPI()
router = APIRouter()
pgdb = PostgresDatabase()


class Dependencies:

    def __init__(self, tokenclass):
        self.token = tokenclass

    async def authentication(self, request: Request):
        try:
            access_token, refresh_token = request.cookies["access_token"], request.cookies["refresh_token"]
            username = await self.token.verify_token(access_token=access_token,
                                                     refresh_token=refresh_token)
            return username
        except KeyError:
            authentication_url = sorted(router.routes, key=lambda x: x.name == "AuthenticationAPI")[0]
            return RedirectResponse(authentication_url)

    @staticmethod
    async def create_user_get_response(user: Users):
        response_data = UserGetResponse(
            username=user.username,
            email=user.email,
            number=user.number,
            age=user.age,
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )
        return response_data


@cbv(router)
class UsersCBV:

    session: AsyncGenerator = Depends(pgdb.get_async_session)
    logs: logging.getLogger = Depends(Logger(__name__).get_logger)
    token = Token()
    dependencies = Dependencies(token)
    redis_cache: RedisDatabase = Depends(RedisDatabase.get_async_client)

    @router.post('/users/registration', name="RegistrationAPI")
    async def user_registration(self, user: RegistrationValidation) -> JSONResponse:
        await asyncio.gather(user.set_hash_password(), user.set_phone_number())
        user, access_token, refresh_token = await asyncio.gather(
            UsersDDL.create_user(user, self.session),
            self.token.create_access_token(user.username),
            self.token.create_refresh_token(user.username)
        )
        response_data = await self.dependencies.create_user_get_response(user)
        response = JSONResponse(content=response_data.dict(), status_code=201)
        response.set_cookie("access_token", access_token)
        response.set_cookie("refresh_token", refresh_token)
        self.logs.info(f"{user.username} was register")
        return response

    @router.get('/users/get_user', name="GetUserApi")
    async def get_user(self, login: str) -> JSONResponse:
        user = await UsersDDL.get_user(login, self.session)
        response_data = UserGetResponse(
            username=user.username,
            email=user.email,
            number=user.number,
            age=user.age,
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )
        response = JSONResponse(content=response_data.dict(), status_code=200)
        return response

    @router.put('/users/update')
    async def update_user(self, data: UserUpdateRequest, username = Depends(dependencies.authentication)):
        user = await UsersDDL.update_user(username, data.dict(), self.session)
        response_data = await self.dependencies.create_user_get_response(user)
        return JSONResponse(content=response_data.dict(), status_code = 201)

    @router.post("/users/authentication", name="AuthenticationAPI")
    async def authentication(self, request_user: AuthenticationValidation) -> JSONResponse:
        db_user = await UsersDDL.get_user(request_user.login, self.session)
        if pwd_context.verify(request_user.password, db_user.hashed_password):
            access_token, refresh_token = await asyncio.gather(
                self.token.create_access_token(db_user.username),
                self.token.create_refresh_token(db_user.username)
            )
            await self.token.save_tokens(db_user.username)
            response = JSONResponse({"msg": "authorized"})
            response.set_cookie("access_token", access_token, httponly=True, secure=True)
            response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True)
            return response
        else:
            response = JSONResponse({"msg": "not authorized"})
            return response

    @router.get("/users/current_user")
    async def current_user(self, username: Dependencies = Depends(dependencies.authentication)):
        return True if username else False

    @router.post("/users/O2Auth", name="O2AuthAPI")
    async def o2auth(self, request: Request):
        access_token, refresh_token = request.cookies["access_token"], request.cookies["refresh_token"]
        sub = await self.token.verify_token(access_token=access_token,
                                            refresh_token=refresh_token)
        if sub:
            new_access_token, new_refresh_token = await asyncio.gather(
                self.token.create_access_token(sub),
                self.token.create_refresh_token(sub)
            )
            response = JSONResponse({"msg": "authorized"})
            response.set_cookie("access_token", new_access_token)
            response.set_cookie("refresh_token", new_refresh_token)
            return response
        else:
            authentication_url = sorted(router.routes, key=lambda x: x.name == "AuthenticationAPI")[0]
            return RedirectResponse(authentication_url.path)

    @router.delete("/user/delete", name="UsersDeleteAPI")
    async def delete_user(self, login, request: Request):
        access_token, refresh_token = request.cookies["access_token"], request.cookies["refresh_token"]
        sub = await self.token.verify_token(access_token=access_token,
                                            refresh_token=refresh_token)
        user = await UsersDDL.get_user(sub, self.session)
        if user.username == login or user.is_superuser == 1:
            await UsersDDL.delete_user(login, self.session)
        if user.username != login:
            pass
        if user.is_superuser == 0:
            pass


app.include_router(router)


def start():
    run('main.server:app', port=8000, host='0.0.0.0', reload=True)
