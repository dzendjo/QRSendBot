from mybot import router
from models import User
from data import jinja
import data

from bson.objectid import ObjectId
from rocketgram import commonfilters, ChatType, context, AnswerCallbackQuery, InlineKeyboard
from rocketgram import SendMessage, SendVideo, SendAudio, EditMessageText, UpdateType, MessageType

from pprint import pp
import orjson
import datetime
import asyncio


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.callback('set_lang')
async def download_link():
    await AnswerCallbackQuery(context.update.callback_query.query_id).send()

    lang = context.update.callback_query.data.split()[-1]
    user = await User.find_one(context.user.user_id)

    user.language = lang
    await user.commit()

    T = data.get_t(user.language)
    data.current_T.set(T)
    await SendMessage(context.user.user_id, T('start/mt')).send()