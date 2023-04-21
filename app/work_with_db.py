from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Advertisment, User, Base
from sqlalchemy import select
from asyncio import run
from os import getenv


DB_NAME = getenv('POSTGRES_DB')
DB_USER = getenv('POSTGRES_USER')
DB_PASSWORD = getenv('POSTGRES_PASSWORD')
HOST = 'postgresql_db'
PORT = '5432'


DSN = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{HOST}:{PORT}/{DB_NAME}'
engine = create_async_engine(DSN)
Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class DataBase:

    def __init__(self, DSN):
        self.DSN = DSN
        self.engine = engine
        self.Session = Session

    async def create_object(self, model, **kwargs):
        async with self.Session() as session:
            new_object = model(**kwargs)
            session.add(new_object)
            await session.commit()

    async def get_object(self, model, item_id, to_dict=False):
        async with self.Session() as session:
            object_ = await session.get(model, item_id)
            if object_ and to_dict:
                return object_.to_dict()
            return object_

    async def update_object(self, model, item_id, **kwargs):
        async with self.Session() as session:
            object_ = await self.get_object(model, item_id)
            for field, value in kwargs.items():
                setattr(object_, field, value)
            session.add(object_)
            await session.commit()

    async def delete_object(self, model, item_id):
        obj = await self.get_object(model, item_id)
        async with self.Session() as session:
            await session.delete(obj)
            await session.commit()

    async def get_user_by_email(self, email):
        async with self.Session() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar()


    async def check_rights_on_adv(self, user_id, adv_id):
        async with self.Session() as session:
            result = await session.execute(select(User).join(Advertisment).where(User.id == user_id,
                                                                                 Advertisment.id == adv_id))
            return result.scalar()



async def create_tables():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def dispose():
    await engine.dispose()


if __name__ == '__main__':
    run(create_tables())
else:
    db = DataBase(DSN)
