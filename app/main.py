import json
from aiohttp import web
from pydantic import ValidationError
from app_errors import HttpError, IntegrityError
from response_statuses import Status
from models import User, Advertisment
from validators import PostAdv, PatchAdv, PostUser, PatchUser
from work_with_db import db, create_tables, dispose
from authenticate import get_hashed_password, check_password



# settings


async def orm_context(app):
    await create_tables()
    yield
    await dispose()


app = web.Application()

app.cleanup_ctx.append(orm_context)

# error handlers

# @app.errorhandler(HttpError)
# def http_error_handler(error):
#     return __error_message(error.message, error.status_code)
#
#
# @app.errorhandler(IntegrityError)
# def integrity_error_handler(error):
#     return __error_message('Error of existance', 409)


# work with objects, validate, authenticate

def validate(json, validate_model_class):
    try:
        model = validate_model_class(**json)
        validated_json = model.dict(exclude_none=True)
        if not validated_json:
            raise web.HTTPBadRequest(text=json.dumps({'error': 'Validation error'}), content_type='application/json')
        return validated_json
    except ValidationError as error:
        raise web.HTTPBadRequest(text=json.dumps({'error': error.errors()}), content_type='application/json')


async def get_object_and_check(model, attr, value, to_dict=True):
    object = await db.get_object_by_attr(model, attr, value, to_dict=to_dict)
    if object is None:
        raise  web.HTTPNotFound(text=json.dumps({'error': f'{model.__name__} not found'}), content_type='application/json')
    return object


async def authenticate(request: web.Request):
    email = request.headers.get('email')
    password = request.headers.get('password')
    if not email or not password:
        raise web.HTTPBadRequest(text=json.dumps({'error': 'Empty email or password'}), content_type='application/json')
    user = await db.get_object_by_attr(User, 'email', email)
    if not user or not check_password(password, user.password):
        raise web.HTTPNotAcceptable(text=json.dumps({'error': 'Invalid authenticate'}), content_type='application/json')
    return user


async def get_user_checked_request(request: web.Request, validate_model):
    json = await request.json()
    validated_json = validate(json, validate_model)
    if 'password' in validated_json:
        hashed_password = get_hashed_password(validated_json['password'])
        validated_json['password'] = hashed_password
    return validated_json


async def get_adv_checked_request(request: web.Request, validate_model):
    user = await authenticate(request)
    json = await request.json()
    validated_json = validate(json, validate_model)
    return user, validated_json


async def check_adv_owner(user_id, adv_id):
    if not await db.check_rights_on_adv(user_id, adv_id):
        raise web.HTTPForbidden(text=json.dumps({'error': 'Can not manipulate with this advertisment'}),
                                content_type='application/json')


def _non_ascii_response(json_, **kwargs):
    response = web.Response(text=json.dumps(json_, ensure_ascii=False), content_type='application/json', **kwargs)
    return response


# views

class UserView(web.View):
    async def get(self):
        user_id = int(self.request.match_info['user_id'])
        user = await get_object_and_check(User, 'id', user_id)
        return _non_ascii_response(user | Status.ok)

    async def post(self):
        validated_json = await get_user_checked_request(self.request, PostUser)
        try:
            await db.create_object(User, **validated_json)
        except IntegrityError:
            raise web.HTTPConflict(text=json.dumps({'error': 'Existance error'}), content_type='application/json')
        del validated_json['password']
        return _non_ascii_response(validated_json | Status.ok)

    async def patch(self):
        validated_json = await get_user_checked_request(self.request, PatchUser)
        user_id = int(self.request.match_info['user_id'])
        user = await get_object_and_check(User, 'id', user_id)
        await db.update_object(User, user_id, **validated_json)
        if 'password' in validated_json:
            del validated_json['password']
        return _non_ascii_response(validated_json | Status.ok)

    async def delete(self):
        user_id = int(self.request.match_info['user_id'])
        user = await get_object_and_check(User, 'id', user_id)
        await db.delete_object(User, user_id)
        return _non_ascii_response(user | Status.ok)


class AdvView(web.View):
    async def get(self):
        adv_id = int(self.request.match_info['adv_id'])
        adv = await get_object_and_check(Advertisment, 'id', adv_id)
        return _non_ascii_response(adv | Status.ok)

    async def post(self):
        user, validated_json = await get_adv_checked_request(self.request, PostAdv)
        validated_json['owner_id'] = user.id
        try:
            await db.create_object(Advertisment, **validated_json)
        except IntegrityError:
            raise web.HTTPConflict(text=json.dumps({'error': 'Existance error'}), content_type='application/json')
        return _non_ascii_response(validated_json | Status.ok)

    async def patch(self):
        adv_id = int(self.request.match_info['adv_id'])
        user, validated_json = await get_adv_checked_request(self.request, PatchAdv)
        await check_adv_owner(user.id, adv_id)
        await db.update_object(Advertisment, adv_id, **validated_json)
        return _non_ascii_response(validated_json | Status.ok)

    async def delete(self):
        adv_id = int(self.request.match_info['adv_id'])
        user = await authenticate(self.request)
        await check_adv_owner(user.id, adv_id)
        await db.delete_object(Advertisment, adv_id)
        message = {'advertisment': adv_id}
        return _non_ascii_response(message | Status.ok)


# urls

app.add_routes([web.post('/user', UserView),
                web.get(r'/user/{user_id:\d+}', UserView),
                web.patch(r'/user/{user_id:\d+}', UserView),
                web.delete(r'/user/{user_id:\d+}', UserView),

                web.post('/advertisment', AdvView),
                web.get(r'/advertisment/{adv_id:\d+}', AdvView),
                web.patch(r'/advertisment/{adv_id:\d+}', AdvView),
                web.delete(r'/advertisment/{adv_id:\d+}', AdvView)])


# Start project

if __name__ == '__main__':
    web.run_app(app)
