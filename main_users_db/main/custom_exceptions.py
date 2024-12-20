from fastapi import HTTPException


class NotAuthorized(HTTPException):
    pass
