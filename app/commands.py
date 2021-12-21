import data
from data import jinja
from mybot import router
from models import Advert
from draw import start_draw

import orjson
import asyncio
import re
import datetime
import secrets
import aiohttp
from pprint import pp

from rocketgram import InlineKeyboard, SendMediaGroup, InputMediaPhoto, EditMessageText
from rocketgram import SendMessage, SendPhoto, DeleteMessage, UpdateType, MessageType
from rocketgram import commonfilters, ChatType, context, priority, SendAudio, commonwaiters
from rocketgram.errors import RocketgramRequest400Error
from bson.objectid import ObjectId


url_pattern = re.compile(r'(?P<url>https?://[^\s]+)')


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.command('/draw')
async def start_message():
    if context.user.user_id not in data.admins:
        return

    T = data.current_T.get()

    async with aiohttp.ClientSession() as session:
        body = {"bot_hash": data.ad_hash, "type": "draw"}
        available_campaigns = {}
        async with session.post(data.api_url_available_campaigns, json=body) as resp:
            resp_json = await resp.json()
            if resp_json['result']:
                available_campaigns = resp_json['available-campaigns']
            else:
                await SendMessage(context.user.user_id, resp_json['error']).send()
                return

    print(available_campaigns)
    total = 0
    for campaign_name, item in available_campaigns.items():
        total += item['ordered_count'] - item['done_count']
    mt = T('draw/mt', campaigns=available_campaigns, total=total)
    await SendMessage(context.user.user_id, mt).send()

    yield commonwaiters.next_message()

    if context.message.text == 'start':
        # Create task for draw
        asyncio.create_task(start_draw(context.user.user_id, list(available_campaigns.keys())[0]))
        await SendMessage(context.user.user_id, T('draw/start_draw_mt')).send()
    else:
        await SendMessage(context.user.user_id, T('draw/not_start_draw_mt')).send()


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.command('/start')
async def start_message():
    mt = jinja.get_template('start/lang').render()

    kb = InlineKeyboard()
    kb.callback('🇷🇺 Русский', 'set_lang ru')
    kb.callback('🇺🇸 English', 'set_lang en')
    kb.arrange_simple(2)

    await SendMessage(context.user.user_id, mt, reply_markup=kb.render()).send()


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.command('/help')
async def start_message():
    T = data.current_T.get()
    await SendMessage(context.user.user_id, T('help'), disable_web_page_preview=True).send()
