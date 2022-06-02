from mybot import router
from models import User, QRCode
from data import jinja
import data
from keyboards import get_qr_ik
import tools

from bson.objectid import ObjectId
from rocketgram import commonfilters, ChatType, context, AnswerCallbackQuery, InputFile, ParseModeType
from rocketgram import SendMessage, SendPhoto, InputMediaPhoto, EditMessageMedia, InlineKeyboard
from rocketgram.errors import RocketgramRequest400Error

from pprint import pp
import orjson
import datetime
from io import BytesIO
import re


url_pattern = re.compile(r'(?P<url>(mailto:|https?:\/\/)(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#()?&//=]*))')


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.callback('set_lang')
async def download_link():
    await AnswerCallbackQuery(context.update.callback_query.id).send()

    lang = context.update.callback_query.data.split()[-1]
    user = await User.find_one(context.user.id)

    user.language = lang
    await user.commit()

    T = data.get_t(user.language)
    data.current_T.set(T)
    await SendMessage(context.user.id, T('start/mt')).send()


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.callback('go_with_sign')
async def download_link():
    await AnswerCallbackQuery(context.update.callback_query.id).send()
    _, qr_id = context.update.callback_query.data.split()
    user = data.current_user.get()
    T = data.get_t(user.language)

    qr = await QRCode.find_one(ObjectId(qr_id))
    qr.is_active_with_sign = True
    await qr.commit()

    kb = get_qr_ik(qr.id, T)

    try:
        await EditMessageMedia(InputMediaPhoto(qr.qr_with_caption_id),
                               context.user.id,
                               context.message.message_id,
                               reply_markup=kb.render()).send()
    except RocketgramRequest400Error as e:
        pass


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.callback('go_without_sign')
async def download_link():
    await AnswerCallbackQuery(context.update.callback_query.id).send()
    _, qr_id = context.update.callback_query.data.split()
    user = data.current_user.get()
    T = data.get_t(user.language)

    qr = await QRCode.find_one(ObjectId(qr_id))
    qr.is_active_with_sign = False
    await qr.commit()

    kb = get_qr_ik(qr.id, T, active_with_sign=False)

    if not qr.qr_without_caption_id:
        # Create QR Image without caption
        qr_image = tools.create_qr_image(qr.data, without_caption=True)
        img_io = BytesIO()
        qr_image.save(img_io, 'PNG')
        qr_file = InputFile('qr.png', 'image/png', img_io.getvalue())

        m = await EditMessageMedia(InputMediaPhoto(qr_file),
                                   context.user.id,
                                   context.message.message_id,
                                   reply_markup=kb.render()).send()

        # Add without caption file_id to DB
        qr.qr_without_caption_id = m.photo[-1].file_id
        await qr.commit()
    else:
        try:
            await EditMessageMedia(InputMediaPhoto(qr.qr_without_caption_id),
                                   context.user.id,
                                   context.message.message_id,
                                   reply_markup=kb.render()).send()
        except RocketgramRequest400Error as e:
            pass


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.callback('save')
async def download_link():
    await AnswerCallbackQuery(context.update.callback_query.id).send()
    _, qr_id = context.update.callback_query.data.split()
    user = data.current_user.get()
    T = data.get_t(user.language)

    qr = await QRCode.find_one(ObjectId(qr_id))

    # Define caption
    try:
        url = url_pattern.search(qr.data).group('url')
    except AttributeError:
        url = ''

    # Define caption
    caption = T('process/final_caption', url=url)

    # Define image file_id
    qr_file_id = qr.qr_with_caption_id if qr.is_active_with_sign else qr.qr_without_caption_id

    await EditMessageMedia(InputMediaPhoto(qr_file_id, caption=caption, parse_mode=ParseModeType.html),
                           context.user.id,
                           context.message.message_id,
                           reply_markup=InlineKeyboard()).send()

    await qr.remove()

    # Send Advert
    await tools.send_advert_action_message(context.bot, context.user.id)

