from rocketgram import SendMessage, SendVideo, SendAnimation, SendPhoto, SendDocument
from rocketgram import InlineKeyboard, Bot
import data
import aiohttp, asyncio
from models import Advert, User
from itertools import chain
from copy import deepcopy
import tools


async def start_draw(bot: Bot, admin_user_id: int, draw_name: str):
    # Get users for draw
    draw = await Advert.find_one({'name': draw_name})
    if not draw:
        draw = Advert(name=draw_name, admin_user_id=admin_user_id, type='draw')
        await draw.commit()
    done_users_set = set(draw.done_users)
    all_users_set = set()
    async for user in User.find({'is_active': True}, {}):
        all_users_set.add(user.id)

    users_for_draw = all_users_set.difference(done_users_set)

    def slice_list(source_list: list, slice_count: int):
        result_list = []
        for i in range(1, len(source_list) + 1):
            if i % slice_count == 0:
                result_list.append(source_list[i - slice_count:i])
        ostatok = len(result_list) * slice_count
        if source_list[ostatok:]:
            result_list.append(source_list[ostatok:])
        return result_list

    sliced_users = slice_list(list(users_for_draw), 100)

    for user_group in sliced_users:
        results = await tools.send_advert_draw_message(bot, user_group)
        draw.done_users = chain(draw.done_users, user_group)
        await draw.commit()

        for user_id in results['fail']:
            user = await User.find_one(user_id)
            if user:
                user.is_active = False
                await user.commit()

    # Send message to admin about and of the draw
    await data.bot.send(SendMessage(admin_user_id, 'Рассылка закончена!'))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_draw(788886288, 'test'))