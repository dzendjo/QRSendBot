import datetime

import data
from models import User, db
import asyncio
from urllib.parse import urlparse, parse_qs
import re
import json


async def register_user(rg_user):
    now = datetime.datetime.now()

    user = User()
    user.id = rg_user.user_id
    user.created = now
    user.visited = now
    user.username = rg_user.username
    user.first_name = rg_user.first_name
    user.last_name = rg_user.last_name
    user.language_code = rg_user.language_code
    user.language = 'ru' if rg_user.language_code == 'ru' else 'en'

    # print(user)

    await user.commit()
    return user


def to_k(count):

    if count == None:
        return 0

    try:
        if count and isinstance(count, str):
            count = int(count)
    except:
        return 0

    if count > 1000000:
        return f'{count // 1000000}.{str(count % 1000000)[0]}M'
    elif count > 1000:
        return f'{count // 1000}.{str(count % 1000)[0]}K'
    else:
        return count


def to_mb(count, need_sep=True):

    if count == None or count == 0:
        return ''

    try:
        if count and isinstance(count, str):
            count = int(count)
    except:
        return 0

    first_part = ''
    if need_sep:
        first_part = '- '

    if count > 1024 * 1024:
        return f'{first_part}{count // (1024 * 1024)}.{str(count % (1024 * 1024))[0]}MB'
    elif count > 1024:
        return f'{first_part}{count // 1024}.{str(count % 1024)[0]}KB'
    else:
        return f'{first_part}{count}B'


def to_t(seconds):
    hours = seconds // 60 // 60
    seconds = seconds - hours * 60 * 60
    minutes = seconds // 60
    seconds = seconds - minutes * 60

    result = list()

    if hours:
        result.append("%02.0f" % hours)

    result.append("%02.0f" % minutes)
    result.append("%02.0f" % seconds)

    return ":".join(result)


def sort_by_label(list):
    re_cypher = re.compile('\d*')

    def sort_func(item):
        cypher = re_cypher.search(item['label']).group()
        if cypher:
            return int(cypher)
        else:
            return 2000

    return sorted(list, key=sort_func)


async def get_model_keys(model):
    return list([str(item) for item in model.schema.fields])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

