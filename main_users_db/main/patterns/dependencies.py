import asyncio
from typing import NoReturn

from fastapi import Request
from database.models import Users
from ..custom_exceptions import NotAuthorized
from ..users_models import UserGetResponse

class Dependencies:

    def __init__(self, tokenclass, authentication_url: str, client) -> NoReturn:
        self.token = tokenclass
        self.authentication_url = authentication_url
        self.client = client

    async def authentication(self, request: Request) -> str:
        try:
            access_token= request.cookies["access_token"]
            username = await self.token.verify_access_token(access_token=access_token,
                                                            client=self.client)
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

    async def create_and_save_tokens(self, username: str) -> tuple:
        access_token, refresh_token = await asyncio.gather(
            self.token.create_access_token(username),
            self.token.create_refresh_token(username)
        )
        await self.token.save_tokens(sub=username, client=self.client,
                                     access_token=access_token,
                                     refresh_token=refresh_token)
        return access_token, refresh_token
