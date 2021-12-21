import data
from models import User
from mybot import router
from rocketgram import commonfilters, ChatType, SendMessage
from rocketgram import context


@router.handler
@commonfilters.chat_type(ChatType.private)
@commonfilters.command('/base')
async def start_command():
    if context.user.user_id in data.admins:
        mt = await User.count_documents()
    else:
        mt = data.jinja.get_template('errors/unknown_command').render()

    await SendMessage(context.user.user_id, mt).send()