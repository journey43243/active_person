from fastapi import FastAPI, APIRouter, Depends, Request
from uvicorn import run
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi_utils.cbv import cbv
import asyncio
from typing import AsyncGenerator
from logs.logger import Logger, logging
from database.core import PostgresDatabase, RedisDatabase, RedisDatabaseEnum
from .patterns.dependencies import Dependencies
from .users_models import RegistrationValidation, \
    UserGetResponse, UserUpdateRequest, AuthenticationValidation, pwd_context
from .custom_exceptions import NotAuthorized
from database.users_orm import UsersDDL
from .auth.tokens import Token

app = FastAPI()
router = APIRouter()
pgdb = PostgresDatabase()
redis_db = RedisDatabase(RedisDatabaseEnum.token_base.value)


@cbv(router)
class UsersCBV:
    session: AsyncGenerator = Depends(pgdb.get_async_session)
    logs: logging.getLogger = Depends(Logger(__name__).get_logger)
    token = Token()
    redis_cache: RedisDatabase = Depends(redis_db.get_async_client)
    dependencies = Dependencies(token, "/users/authentication/", redis_db.async_client)

    @router.post('/users/registration/', name="RegistrationAPI")
    async def user_registration(self, user: RegistrationValidation) -> JSONResponse:
        await asyncio.gather(user.set_hash_password(), user.set_phone_number())
        user, tokens = await asyncio.gather(
            UsersDDL.create_user(user, self.session),
            self.dependencies.create_and_save_tokens(user.username)
        )
        access_token, refresh_token = tokens
        response_data = await self.dependencies.create_user_get_response(user)
        response = JSONResponse(content=response_data.model_dump(), status_code=201)
        response.set_cookie("access_token", access_token)
        response.set_cookie("refresh_token", refresh_token)
        self.logs.info(f"{user.username} was register")
        return response



    @router.get('/users/get_user/', name="GetUserApi")
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


    @router.put('/users/update/')
    async def update_user(self, data: UserUpdateRequest, username=Depends(dependencies.authentication)) -> JSONResponse:
        user = await UsersDDL.update_user(username, data.dict(), self.session)
        response_data = await self.dependencies.create_user_get_response(user)
        return JSONResponse(content=response_data.dict(), status_code=201)


    @router.post("/users/authentication/", name="AuthenticationAPI")
    async def authentication(self, request_user: AuthenticationValidation) -> JSONResponse:
        db_user = await UsersDDL.get_user(request_user.login, self.session)
        if pwd_context.verify(request_user.password, db_user.hashed_password):
            access_token, refresh_token = await self.dependencies.create_and_save_tokens(db_user.username)
            response = JSONResponse({"msg": "authorized"})
            response.set_cookie("access_token", access_token, httponly=True, secure=True)
            response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True)
            return response
        else:
            raise NotAuthorized(status_code=401)


    @router.get("/users/current_user/")
    async def current_user(self, request: Request, username: Dependencies = Depends(dependencies.authentication)):
        return username if username else None


    @router.post("/users/O2Auth/", name="O2AuthAPI")
    async def o2auth(self, request: Request):
        try:
            access_token, refresh_token = request.cookies["access_token"], request.cookies["refresh_token"]
        except KeyError:
            raise NotAuthorized(status_code=401)

        sub = await self.token.verify_token(self.redis_cache,
                                            access_token=access_token,
                                            refresh_token=refresh_token)
        new_access_token, new_refresh_token = await asyncio.gather(
            self.token.create_access_token(sub),
            self.token.create_refresh_token(sub)
        )
        response = JSONResponse({"msg": "authorized"})
        response.set_cookie("access_token", new_access_token)
        response.set_cookie("refresh_token", new_refresh_token)
        return response


    @router.delete("/user/delete/", name="UsersDeleteAPI")
    async def delete_user(self, login, request: Request) -> JSONResponse:
        access_token, refresh_token = request.cookies["access_token"], request.cookies["refresh_token"]
        sub = await self.token.verify_token(self.redis_cache,
                                            access_token=access_token,
                                            refresh_token=refresh_token)
        user = await UsersDDL.get_user(sub, self.session)
        if user.username == login or user.is_superuser == 1:
            await UsersDDL.delete_user(login, self.session)
            return JSONResponse(content={"status": True}, status_code=200)
        else:
            raise NotAuthorized


    @app.exception_handler(NotAuthorized)
    async def not_authorized_handler(self, request: Request):
        return JSONResponse({"detail": "Not authorized"}, status_code=401)


app.include_router(router)


def start():
    run('main.server:app', port=8000, host='0.0.0.0', reload=True, workers=5)

