from work_with_db import db
from asyncio import run
from models import User, Advertisment



user_json = {'name': 'Иван', 'email': 'мыло@bk.ru', 'password': 'пароль'}

adv_json = {'owner_id': 2, 'title': 'куплю лук', 'description': 'хороший'}


result = run(db.check_rights_on_adv(2, 4))

print(result)


