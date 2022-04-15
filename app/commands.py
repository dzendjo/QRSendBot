import asyncio
import re
import qrcode
from io import BytesIO
from PIL import ImageDraw, ImageFont, Image
from pyzbar.pyzbar import decode

import aiohttp
from rocketgram import InlineKeyboard, SendPhoto, InputFile, InputMediaPhoto
from rocketgram import SendMessage, UpdateType, MessageType, GetFile
from rocketgram import commonfilters, ChatType, context, commonwaiters

import data
import tools
from data import jinja
from draw import start_draw
from mybot import router
from models import QRCode
from keyboards import get_qr_ik


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


@router.handler
@commonfilters.update_type(UpdateType.message)
@commonfilters.message_type(MessageType.text)
@commonfilters.chat_type(ChatType.private)
async def link_command():
    T = data.current_T.get()

    main_image = tools.create_qr_image(context.message.text)

    # if too big data
    if not main_image:
        await SendMessage(context.user.user_id, T('errors/too_big_data')).send()
        return

    img_io = BytesIO()
    main_image.save(img_io, 'PNG')

    # Add QR to DB
    qr = QRCode(data=context.message.text, user_id=context.user.user_id)
    await qr.commit()

    # Forming keyboard
    kb = get_qr_ik(qr.id, T)

    qr_file = InputFile('qr.png', 'image/png', img_io.getvalue())
    m = await SendPhoto(context.user.user_id, qr_file, reply_markup=kb.render()).send()

    # Save file_id with caption
    qr.qr_with_caption_id = m.photo[-1].file_id
    await qr.commit()


@router.handler
@commonfilters.update_type(UpdateType.message)
@commonfilters.message_type(MessageType.document, MessageType.photo)
@commonfilters.chat_type(ChatType.private)
async def link_command():
    T = data.current_T.get()

    if context.message.photo:
        file_id = context.message.photo[-1].file_id
    elif context.message.document.mime_type in ['image/jpeg', 'image/png', 'image/jpg']:
        file_id = context.message.document.file_id
    else:
        await SendMessage(context.user.user_id, T('errors/not_correct_document')).send()
        return

    response = await GetFile(file_id).send()
    api_file_url = 'https://api.telegram.org/file/bot{}/'.format(context.bot.token)
    url = api_file_url + response.file_path

    session: aiohttp.ClientSession = context.bot.connector._session

    response = await session.get(url)
    file_data = await response.read()

    image = Image.open(BytesIO(file_data))
    try:
        decode_data = decode(image)[0].data.decode()
    except IndexError as e:
        await SendMessage(context.user.user_id, T('errors/cannot_decode_qr')).send()
        return

    await SendMessage(context.user.user_id, decode_data).send()






