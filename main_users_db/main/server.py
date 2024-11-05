from fastapi import FastAPI, APIRouter
from uvicorn import run
from models.users_models import RegistrationValidation, AuthenticationValidation
from database.users_orm import UsersOrm
from database.core import PostgresDatabase
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

app = FastAPI()
router = APIRouter()
pgdb = PostgresDatabase()

@router.post('/users/registrate_user')
async def get_registrate_request(user: RegistrationValidation):
    await user.set_hash_password()
    await user.set_phone_number()
    #try:
    await UsersOrm.create_user(user, pgdb)
    return JSONResponse({"status": 200,
                        "msg": "created"})
    # except IntegrityError:
    #     return JSONResponse({"status": "rejected",
    #                          "msg": "created"})

@router.post('/users/verify_user')
async def verify_user(user: AuthenticationValidation):
    verify_status = await UsersOrm.get_user(user.login, pgdb)
    if not verify_status:
        return JSONResponse({"status": "rejected",
                             "msg": "not verified"})
    else:
        return JSONResponse({"status": "accepted",
                             "msg": "verified"})

app.include_router(router)

def start():
    run('main.server:app', port=8000, host='0.0.0.0', reload=True)
