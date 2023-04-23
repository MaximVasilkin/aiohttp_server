import json
from aiohttp import web
from app_errors import my_http_error
from sqlalchemy.exc import IntegrityError
from response_statuses import Status
from models import User, Advertisment
from validators import PostAdv, PatchAdv, PostUser, PatchUser, validate
from work_with_db import db, create_tables, dispose
from authenticate import get_hashed_password, authenticate


# app, settings

async def orm_context(app):
    await create_tables()
    yield
    await dispose()


@web.middleware
async def orm_middleware(request: web.Request, handler):
    http_method = request.method
    allowed_methods = ('GET', 'PATCH', 'DELETE')
    if http_method in allowed_methods:
        if 'user_id' in request.match_info:
            obj_id = request.match_info.get('user_id')
            model = User
        else:
            obj_id = request.match_info.get('adv_id')
            model = Advertisment
        obj_dict = await get_object_and_check(model, 'id', int(obj_id))
        request['orm_item'] = obj_dict
    response = await handler(request)
    return response


app = web.Application()

app.cleanup_ctx.append(orm_context)
app.middlewares.append(orm_middleware)


# get orm object, check request, custom response

async def get_object_and_check(model, attr, value, to_dict=True):
    object = await db.get_object_by_attr(model, attr, value, to_dict=to_dict)
    if object is None:
        raise my_http_error(web.HTTPBadRequest, f'{model.__name__} not found')
    return object


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
        raise my_http_error(web.HTTPForbidden, 'Can not manipulate with this advertisment')


def _non_ascii_response(json_, **kwargs):
    response = web.Response(text=json.dumps(json_, ensure_ascii=False), content_type='application/json', **kwargs)
    return response


# views

class UserView(web.View):
    async def get(self):
        return _non_ascii_response(self.request['orm_item'] | Status.ok)

    async def post(self):
        validated_json = await get_user_checked_request(self.request, PostUser)
        try:
            await db.create_object(User, **validated_json)
        except IntegrityError:
            raise my_http_error(web.HTTPConflict, 'Existance error')
        del validated_json['password']
        return _non_ascii_response(validated_json | Status.ok)

    async def patch(self):
        validated_json = await get_user_checked_request(self.request, PatchUser)
        await db.update_object(User, self.request['orm_item']['id'], **validated_json)
        if 'password' in validated_json:
            del validated_json['password']
        return _non_ascii_response(validated_json | Status.ok)

    async def delete(self):
        await db.delete_object(User, self.request['orm_item']['id'])
        return _non_ascii_response(self.request['orm_item'] | Status.ok)


class AdvView(web.View):
    async def get(self):
        return _non_ascii_response(self.request['orm_item'] | Status.ok)

    async def post(self):
        user, validated_json = await get_adv_checked_request(self.request, PostAdv)
        validated_json['owner_id'] = user.id
        try:
            await db.create_object(Advertisment, **validated_json)
        except IntegrityError:
            raise my_http_error(web.HTTPConflict, 'Existance error')
        return _non_ascii_response(validated_json | Status.ok)

    async def patch(self):
        user, validated_json = await get_adv_checked_request(self.request, PatchAdv)
        await check_adv_owner(user.id, self.request['orm_item']['id'])
        await db.update_object(Advertisment, self.request['orm_item']['id'], **validated_json)
        return _non_ascii_response(validated_json | Status.ok)

    async def delete(self):
        adv_id = self.request['orm_item']['id']
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


# start project

if __name__ == '__main__':
    web.run_app(app)
