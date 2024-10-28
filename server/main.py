import json
from typing import AsyncGenerator, Annotated
from types import FunctionType

import sqlalchemy
from fastapi import FastAPI, APIRouter
from pydantic_core import PydanticCustomError
from uvicorn import run

from fastapi.responses import JSONResponse
from OAuth2.tokens import Token, jwt
from database.models import UserValidationReg, UserValidationAuth, PhoneNumber
from database.users_orm import UsersOrm, RedisDatabase, PostgresDatabase
from fastapi import Request, Depends
from logger.logger import Logger, logging

app = FastAPI()
register_router = APIRouter()
rdb = RedisDatabase()
pgdb = PostgresDatabase()


@app.post('/users/registration')
async def regist(user: UserValidationReg, logs: Annotated[logging.getLogger,
                                                          Depends(Logger(__name__).get_logger)]):
    try:
        token = Token(user.name)
        await user.set_hash_password()
        await user.set_number()
        await UsersOrm.create_user(user, pgdb)

        access_token = await token.create_access_token()
        refresh_token = await token.create_refresh_token()
        response = JSONResponse({"status": "registered"})
        response.set_cookie("access_token", access_token)
        response.set_cookie("refresh_token", refresh_token)
        logs.info(f"{user.name} was register")
        return response
    except sqlalchemy.exc.IntegrityError:
        logs.error(f'Try to create existing user. User is {user.name}')
        response = JSONResponse({"status": "rejected",
                                 "msg": "user already exists"})
        return response
    except PydanticCustomError:
        response = {"status": "rejected",
                    "msg": "invalid phone number"}
        return response
    # except Exception:
    #     logs.error("Something wrong. Check server logs to find error and fix that")


@app.post('/users/auth')
async def auth_by_user_data(user: UserValidationAuth, logs: Annotated[logging.getLogger,
                                                                      Depends(Logger(__name__).get_logger)]):
    is_auth = await UsersOrm.authenticate_user(user, pgdb)
    try:
        token = Token(is_auth[1])

        if is_auth[0]:
            response = JSONResponse({"Authenticate": "successful"})

            access_token = await token.create_access_token()
            refresh_token = await token.create_refresh_token()
            await token.save_tokens()
            response.set_cookie("access_token", access_token)
            response.set_cookie("refresh_token", refresh_token)
        else:
            response = JSONResponse({"Authenticate": "rejected",
                                     "msg": "wrong password"})
        return response
    except TypeError:
        return JSONResponse({"Authenticate": "user not found"})
    except Exception:
        logs.error("Something wrong. Check server logs to find error and fix that")


@app.get('/users/current_user')
async def current_user(request: Request,
                       logs: Annotated[logging.getLogger,
                                       Depends(Logger(__name__).get_logger)],
                       ):
    token = Token(None)
    try:

        access_token = request.cookies.get('access_token')
        refresh_token = request.cookies.get('refresh_token')
        verify_result = await token.verify_token((access_token, refresh_token))
        print(verify_result)

        if type(verify_result) == bool and not verify_result:

            return {"msg": "You need to authorization"}

        elif type(verify_result) == bool and verify_result:
            token_data = jwt.decode(access_token, token.secret_key, token.algorithm)
            sub = token_data["sub"]
            user = await UsersOrm.get_user(sub, pgdb)
            logs.info(f"{sub} was authorized")
            return f"Hello {user.username}"

        elif type(verify_result) == tuple:

            response = JSONResponse(f"hello {token.sub}")
            response.set_cookie("access_token", verify_result[0])
            response.set_cookie("refresh_token", verify_result[1])
            logs.info(f"{token.sub} was authorized")
            return response

    except Exception:
        logs.error("Something wrong. Check server logs to find error and fix that")
        return 'error'


'''
    I have too many logs. More, than i generate
'''


def start():
    run('server.main:app', port=8000, host='0.0.0.0', reload=True)
