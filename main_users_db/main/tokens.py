import datetime
import os
import jwt
from database.core import RedisDatabase
import json
from fastapi import HTTPException
from typing import Union


class Token:

    def __init__(self, cache=RedisDatabase()):
        self.iss = "active_person_OAuth2"
        self.access_token = None
        self.refresh_token = None
        self.cache = cache
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
        self.access_token = access_token
        return self.access_token

    async def create_refresh_token(self, sub):
        token_type = "refresh"
        token_data = {"sub": sub,
                      "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=self.exp_time_refresh),
                      "iss": self.iss,
                      "token_type": token_type}
        refresh_token = jwt.encode(token_data, self.secret_key, self.algorithm)
        self.refresh_token = refresh_token
        return self.refresh_token

    async def save_tokens(self):
        async with self.cache.get_async_client() as client:
            await client.set(self.sub, json.dumps([self.access_token, self.refresh_token]))

    async def check_cache(self, sub):
        async with self.cache.get_async_client() as client:
            tokens_couple = await client.get(sub)
            return tokens_couple

    async def verify_token(self, *, access_token, refresh_token) -> str:
        try:
            decoded_token = jwt.decode(access_token, self.secret_key, self.algorithm)
            sub = await self.check_cache(decoded_token["sub"])
            if sub:
                return decoded_token["sub"]
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
        except jwt.exceptions.ExpiredSignatureError:
            pass
        try:
            decoded_token = jwt.decode(refresh_token, self.secret_key, self.algorithm)
            sub = await self.check_cache(decoded_token["sub"])
            if sub:
                return decoded_token["sub"]
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
        except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
            raise HTTPException(status_code=401, detail="Invalid token")
