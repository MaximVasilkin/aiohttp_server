from bcrypt import hashpw, gensalt, checkpw
from aiohttp import web
from models import User
from work_with_db import db
from app_errors import my_http_error


def get_hashed_password(password: str):
    password = password.encode()
    password = hashpw(password, salt=gensalt())
    password = password.decode()
    return password


def check_password(password: str, hashed_password: str) -> bool:
    return checkpw(password.encode(), hashed_password.encode())


async def authenticate(request: web.Request):
    email = request.headers.get('email')
    password = request.headers.get('password')
    if not email or not password:
        raise my_http_error(web.HTTPBadRequest, 'Empty email or password')
    user = await db.get_object_by_attr(User, 'email', email)
    if not user or not check_password(password, user.password):
        raise my_http_error(web.HTTPNotAcceptable, 'Invalid authenticate')
    return user
