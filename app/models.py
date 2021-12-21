import datetime
import os

from motor.motor_asyncio import AsyncIOMotorClient
from umongo import Document, fields
from umongo.frameworks import MotorAsyncIOInstance


db_host = os.environ.get('DB_HOST', 'localhost')
db = AsyncIOMotorClient(f'mongodb://{db_host}:27017')['BOT_TEMPLATE']
instance = MotorAsyncIOInstance(db)


@instance.register
class Advert(Document):
    class Meta:
        collection_name = 'adverts'
        indexes = []

    date = fields.DateTimeField(default=datetime.datetime.now())
    name = fields.StrField(required=True, unique=True)
    type = fields.StrField(allow_none=True)
    done_users = fields.ListField(fields.IntField, default=[])
    admin_user_id = fields.IntField(required=True)


@instance.register
class User(Document):
    class Meta:
        collection_name = 'botusers'
        indexes = ['is_active']

    id = fields.IntField(attribute='_id')
    process_flag = fields.BooleanField(default=False)
    created = fields.DateTimeField(required=True)
    visited = fields.DateTimeField(required=True)
    username = fields.StrField(required=True, allow_none=True)
    first_name = fields.StrField(required=True)
    last_name = fields.StrField(required=True, allow_none=True)
    language_code = fields.StrField(required=True, allow_none=True)
    language = fields.StrField(required=True)
    is_active = fields.BooleanField(default=True)


async def create_indexes():
    await User.ensure_indexes()


if __name__ == '__main__':
    pass
