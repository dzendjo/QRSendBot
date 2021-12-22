import datetime

# import data
from models import User, db
import asyncio
from urllib.parse import urlparse, parse_qs
import re
import json
import qrcode
from PIL import ImageDraw, ImageFont, Image, ImageOps
from io import BytesIO
from string import ascii_letters
import textwrap


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


def create_qr_image(caption, without_caption=False):
    try:
        qr_img = qrcode.make(caption)
    except qrcode.exceptions.DataOverflowError:
        return None

    if without_caption:
        return qr_img

    # Determine font
    font = ImageFont.truetype("UbuntuMono-Regular.ttf", 16)

    # Determine count of letters for current img size
    avg_char_width = sum(font.getsize(char)[0] for char in ascii_letters) / len(ascii_letters)
    max_char_count = int(((qr_img.size[0] * .95) - 80) / avg_char_width)

    # Create a wrapped text object using scaled character count
    lines = textwrap.wrap(caption, width=max_char_count)
    optimized_caption = '\n'.join(lines)

    # Create base text image
    text_img = Image.new('RGB', (qr_img.size[0], 16), color='white')
    draw = ImageDraw.Draw(text_img)

    # Define text block sizes
    text_block_width, text_block_height = draw.multiline_textsize(optimized_caption, font=font)

    # Create text image
    text_img = Image.new('RGB', (qr_img.size[0], text_block_height + 40), color='white')
    draw = ImageDraw.Draw(text_img)
    draw.multiline_text(((qr_img.size[0] - text_block_width) / 2, 20), optimized_caption, font=font, fill=(0, 0, 0))
    cur_x = 0
    cur_y = 0
    for x in range(cur_x, qr_img.size[0], 8):
        draw.line([(x, cur_y), (x + 4, cur_y)], fill=(0, 0, 0), width=6)

    # Unite images to final image
    main_image = Image.new('RGB', (qr_img.size[0], qr_img.size[1] + text_img.size[1]), (250, 250, 250))
    main_image.paste(qr_img, (0, 0))
    main_image.paste(text_img, (0, qr_img.size[1]))
    return main_image


if __name__ == '__main__':
    create_qr_by_url('https://www.youtube.com/watch?v=r_pwpQeBU7A')

