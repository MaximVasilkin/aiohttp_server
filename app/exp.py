from work_with_db import db
from asyncio import run, WindowsSelectorEventLoopPolicy, set_event_loop_policy
from models import User, Advertisment
set_event_loop_policy(WindowsSelectorEventLoopPolicy())


user_json = {'name': 'Иван', 'email': 'мыло@bk.ru', 'password': 'пароль'}

adv_json = {'owner_id': 2, 'title': 'куплю лук', 'description': 'хороший'}


result = run(db.get_object_by_attr(Advertisment, 'id', 3))

print(result.user)

