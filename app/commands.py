import asyncio
import re
import qrcode
from io import BytesIO
from PIL import ImageDraw, ImageFont, Image
from pyzbar.pyzbar import decode
import regex

import aiohttp
from rocketgram import InlineKeyboard, SendPhoto, InputFile, SendVideo, SendAnimation
from rocketgram import SendMessage, UpdateType, MessageType, GetFile, SendLocation
from rocketgram import commonfilters, ChatType, context, commonwaiters, Bot


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
    if context.user.id not in data.admins:
        return

    T = data.current_T.get()
    available_campaigns = {}

    async with aiohttp.ClientSession() as session:
        headers = {'token': data.ad_token}

        async with session.post(data.api_url_available_campaigns, headers=headers) as resp:
            resp_json = await resp.json()
            if resp_json['result']:
                available_campaigns = resp_json['draw']
            else:
                await SendMessage(context.user.id, resp_json['error']).send()
                return

    if not available_campaigns:
        await SendMessage(context.user.id, T('draw/no_campaigns_mt')).send()
        return

    mt = T('draw/mt', campaigns=available_campaigns)
    await SendMessage(context.user.id, mt).send()

    yield commonwaiters.next_message()

    if context.message.text.lower() == 'start':
        # Create task for draw
        raw_campaign_name = '-'.join(available_campaigns.keys())
        campaign_name = regex.sub(r'\P{posix_alnum}+', '-', raw_campaign_name).strip('-')
        asyncio.create_task(start_draw(context.bot, context.user.id, campaign_name))
        await SendMessage(context.user.id, T('draw/start_draw_mt')).send()
    else:
        await SendMessage(context.user.id, T('draw/not_start_draw_mt')).send()


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.command('/start')
async def start_message():
    mt = jinja.get_template('start/lang').render()

    kb = InlineKeyboard()
    kb.callback('🇷🇺 Русский', 'set_lang ru')
    kb.callback('🇺🇸 English', 'set_lang en')
    kb.arrange_simple(2)

    await SendMessage(context.user.id, mt, reply_markup=kb.render()).send()


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.command('/help')
async def start_message():
    T = data.current_T.get()
    await SendMessage(context.user.id, T('help'), disable_web_page_preview=True).send()


@router.handler
@commonfilters.update_type(UpdateType.message)
@commonfilters.message_type(MessageType.text)
@commonfilters.chat_type(ChatType.private)
async def link_command():
    T = data.current_T.get()

    main_image = tools.create_qr_image(context.message.text)

    # if too big data
    if not main_image:
        await SendMessage(context.user.id, T('errors/too_big_data')).send()
        return

    img_io = BytesIO()
    main_image.save(img_io, 'PNG')

    # Add QR to DB
    qr = QRCode(data=context.message.text, user_id=context.user.id)
    await qr.commit()

    # Forming keyboard
    kb = get_qr_ik(qr.id, T)

    qr_file = InputFile('qr.png', 'image/png', img_io.getvalue())
    m = await SendPhoto(context.user.id, qr_file, reply_markup=kb.render()).send()

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
        await SendMessage(context.user.id, T('errors/not_correct_document')).send()
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
        await SendMessage(context.user.id, T('errors/cannot_decode_qr')).send()
        return

    if decode_data[:5].lower() == 'wifi:':
        items = decode_data[5:].split(';')
        net_name, password, encryption = '', '', ''
        for item in items:
            if item:
                if item[0] == 'S':
                    net_name = item.split(':')[1]
                elif item[0] == 'T':
                    encryption = item.split(':')[1]
                elif item[0] == 'P':
                    password = item.split(':')[1]
        await SendMessage(context.user.id,
                          T('rec/wifi', net_name=net_name, encryption=encryption, password=password)).send()
    elif decode_data[:4].lower() == 'tel:':
        # tel: +78005553535
        tel = decode_data.split(':')[1].strip()
        await SendMessage(context.user.id, T('rec/tel', tel=tel)).send()
    elif decode_data[:4].lower() == 'geo:':
        # geo: 40.71872, -73.98905
        items = decode_data[4:].split(',')
        latitude = items[0].strip()
        longitude = items[1].strip()
        await SendLocation(context.user.id, latitude=latitude, longitude=longitude).send()
        await SendMessage(context.user.id, T('rec/geo', latitude=latitude, longitude=longitude)).send()

    else:
        await SendMessage(context.user.id, decode_data).send()

    # Send Advert
    await tools.send_advert_action_message(context.bot, context.user.id)
