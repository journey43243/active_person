async def regist(user: UserValidationReg, logs: Annotated[logging.getLogger,
                                                          Depends(Logger(__name__).get_logger)]):
    try:
        token = Token(user.name)
        await user.set_hash_password()
        await user.set_number()
        #запросить создание юсера у бд
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