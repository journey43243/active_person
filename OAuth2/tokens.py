import datetime

import jwt
from database.models import Mixin
from database.core import RedisDatabase
import json


class Token(Mixin):

    def __init__(self, sub, cache=RedisDatabase()):
        self.sub = sub
        self.iss = "active_person_OAuth2"
        self.access_token = None
        self.refresh_token = None
        self.cache = cache

    async def create_access_token(self):
        token_type = "access"
        token_data = {"sub": self.sub,
                      "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=self.exp_time_access),
                      "iss": self.iss,
                      "token_type": token_type}
        access_token = jwt.encode(token_data, self.secret_key, self.algorithm)
        self.access_token = access_token
        return self.access_token

    async def create_refresh_token(self):
        token_type = "refresh"
        token_data = {"sub": self.sub,
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

    async def verify_token(self, tokens_couple: tuple):
        '''
        :param tokens_couple:
        :return: tuple len == 1 with bool value
        if user not authenticated or we need to send to user
        new couple of access token and refresh token
        '''

        try:
            decoded_token = jwt.decode(tokens_couple[0], self.secret_key, self.algorithm)
            sub = await self.check_cache(decoded_token["sub"])
            if sub:
                return True
            else:
                return False
        except jwt.exceptions.ExpiredSignatureError:
            try:
                decoded_token = jwt.decode(tokens_couple[1], self.secret_key, self.algorithm)
                sub = await self.check_cache(decoded_token["sub"])
                if sub:
                    self.sub = decoded_token["sub"]
                    self.access_token = await self.create_access_token()
                    self.refresh_token = await self.create_refresh_token()
                    await self.save_tokens()
                    return self.access_token, self.refresh_token, self.sub
                else:
                    return False
            except jwt.exceptions.ExpiredSignatureError:
                return False
        except jwt.exceptions.InvalidSignatureError:
            return False
        except jwt.exceptions.DecodeError:
            return False
