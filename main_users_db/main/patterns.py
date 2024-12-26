import asyncio
from fastapi import Request
from database.models import Users
from fastapi.responses import RedirectResponse, JSONResponse
from .custom_exceptions import NotAuthorized
from .users_models import UserGetResponse

class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Dependencies:

    def __init__(self, tokenclass, authentication_url):
        self.token = tokenclass
        self.authentication_url = authentication_url

    async def authentication(self, request: Request):
        try:
            access_token, refresh_token = request.cookies["access_token"], request.cookies["refresh_token"]
            username = await self.token.verify_token(access_token=access_token,
                                                     refresh_token=refresh_token)
            return username
        except KeyError:
            raise NotAuthorized(status_code=401)

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

    async def create_and_save_tokens(self, username, client):
        access_token, refresh_token = await asyncio.gather(
            self.token.create_access_token(username),
            self.token.create_refresh_token(username)
        )
        await self.token.save_tokens(username, client,
                                     access_token=access_token,
                                     refresh_token=refresh_token)
        return access_token, refresh_token