from fastapi import FastAPI


app = FastAPI()


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