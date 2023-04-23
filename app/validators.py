from pydantic import BaseModel, validator, EmailStr, ValidationError
from typing import Optional
from aiohttp import web
from app_errors import my_http_error


def validate(json, validate_model_class):
    try:
        model = validate_model_class(**json)
        validated_json = model.dict(exclude_none=True)
        if not validated_json:
            raise my_http_error(web.HTTPBadRequest, 'Validation error')
        return validated_json
    except ValidationError as error:
        raise my_http_error(web.HTTPBadRequest, error.errors())


def _check_text_len(text, min_len, max_len, description):
    len_text = len(text)
    if len_text > max_len or len_text < min_len:
        raise ValueError(f'Incorrect length of {description}')


def is_acceptable_password(password, min_len, max_len):
    return 'password' not in password.lower()\
           and max_len >= len(password) >= min_len \
           and any(map(lambda x: x.isdigit(), password)) \
           and not password.isdigit()


class AbcUser(BaseModel):
    name: str
    password: str

    @validator('name')
    def validate_name(cls, value):
        if not value.isalpha():
            raise ValueError('Name should contain only letters')
        return value

    @validator('password')
    def validate_password(cls, value):
        if not is_acceptable_password(value, 8, 99):
            raise ValueError('Too easy password')
        return value


class PostUser(AbcUser, BaseModel):
    email: EmailStr


class PatchUser(AbcUser, BaseModel):
    name: Optional[str]
    password: Optional[str]


class AbcAdv(BaseModel):
    title: str
    description: str

    @validator('title')
    def validate_title(cls, value):
        _check_text_len(value, 5, 70, 'title')
        return value

    @validator('description')
    def validate_description(cls, value):
        _check_text_len(value, 10, 500, 'description')
        return value


class PostAdv(AbcAdv, BaseModel):
    pass


class PatchAdv(AbcAdv, BaseModel):
    title: Optional[str]
    description: Optional[str]
