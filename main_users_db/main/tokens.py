import datetime
import os
import jwt
from database.core import RedisDatabase
import json
from .custom_exceptions import NotAuthorized
from .patterns import Singleton
import asyncio


class Token(metaclass=Singleton):

    def __init__(self):
        self.iss = "active_person_OAuth2"
        self.exp_time_access = int(os.environ.get("EXPIRE_TIME_ACCESS"))
        self.exp_time_refresh = int(os.environ.get("EXPIRE_TIME_REFRESH"))
        self.algorithm = os.environ.get("ALGORITHM")
        self.secret_key = os.environ.get("SECRET_KEY")

    async def create_access_token(self, sub):
        token_type = "access"
        token_data = {"sub": sub,
                      "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=self.exp_time_access),
                      "iss": self.iss,
                      "token_type": token_type}
        access_token = jwt.encode(token_data, self.secret_key, self.algorithm)
        return access_token

    async def create_refresh_token(self, sub):
        token_type = "refresh"
        token_data = {"sub": sub,
                      "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=self.exp_time_refresh),
                      "iss": self.iss,
                      "token_type": token_type}
        refresh_token = jwt.encode(token_data, self.secret_key, self.algorithm)
        return refresh_token

    @staticmethod
    async def save_tokens(sub, client, *, access_token, refresh_token):
        await client.set(sub, json.dumps([access_token, refresh_token]))

    @staticmethod
    async def check_cache(sub, client):
        tokens_couple = await client.get(sub)
        return tokens_couple

    async def verify_access_token(self, access_token, client):
        try:
            decoded_token = jwt.decode(access_token, self.secret_key, self.algorithm)
            sub = await self.check_cache(decoded_token["sub"], client)
            if sub:
                return decoded_token["sub"]
            else:
                return False
        except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
            return False

    async def verify_refresh_token(self, refresh_token, client):
        try:
            decoded_token = jwt.decode(refresh_token, self.secret_key, self.algorithm)
            sub = await self.check_cache(decoded_token["sub"], client)
            if sub:
                return decoded_token["sub"]
            else:
                return False
        except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
            return False

    async def verify_token(self, client, *, access_token, refresh_token) -> str:
        verify_results = await asyncio.gather(
            self.verify_access_token(access_token, client),
            self.verify_refresh_token(refresh_token, client)
        )
        sub = [i for i in verify_results if i]
        if sub:
            return sub[0]
        else:
            raise NotAuthorized(status_code=401, detail="Not authorized")