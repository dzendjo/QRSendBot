import logging
import os
import asyncio

import statistics
import callbacks
import commands
import keyboards
import mybot
import rocketgram
import unknown
import data
from templates import templates
import models

import j2tools
import jinja2
import jinja2.ext
from tools import to_t, to_k

from nats.aio.client import Client as NATS


# avoid to remove "unused" imports by optimizers
def fix_imports():
    _ = callbacks
    _ = commands
    _ = keyboards
    _ = unknown
    _ = statistics


logger = logging.getLogger('minibots.engine')


async def connect_nats(loop, nats_server):
    nc = NATS()
    if not data.NATS_TOKEN:
        await nc.connect(nats_server, loop=loop)
    else:
        await nc.connect(nats_server, loop=loop, token=data.NATS_TOKEN)
    return nc


def main():
    mode = os.environ.get('MODE')
    if mode is None and 'DYNO' in os.environ:
        mode = 'heroku'

    if mode not in ('updates', 'webhook', 'heroku'):
        raise TypeError('MODE must be `updates` or `webhook` or `heroku`!')

    logging.basicConfig(format='%(asctime)s - %(levelname)-5s - %(name)-25s: %(message)s')
    logging.basicConfig(level=logging.ERROR)
    logging.getLogger('engine').setLevel(logging.INFO)
    logging.getLogger('mybot').setLevel(logging.DEBUG)
    logging.getLogger('rocketgram').setLevel(logging.DEBUG)
    logging.getLogger('rocketgram.raw.in').setLevel(logging.INFO)
    logging.getLogger('rocketgram.raw.out').setLevel(logging.INFO)

    logger.info('Starting bot''s template in %s...', mode)

    bot = mybot.get_bot(os.environ['TOKEN'].strip())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(models.create_indexes())

    # Run NATS
    # data.nc = loop.run_until_complete(connect_nats(loop, data.NATS_SERVER_URI))

    data.bot = bot

    _loader = jinja2.PrefixLoader({k: j2tools.YamlLoader(v) for k, v in templates.items()})
    _jinja = jinja2.Environment(loader=_loader)
    _jinja.filters['to_t'] = to_t
    _jinja.filters['to_k'] = to_k
    data.get_t = j2tools.t_factory(_jinja)

    if mode == 'updates':
        rocketgram.UpdatesExecutor.run(bot, drop_pending_updates=bool(int(os.environ.get('DROP_UPDATES', 0))))
    else:
        port = int(os.environ['PORT']) if mode == 'heroku' else int(os.environ.get('WEBHOOK_PORT', 8080))
        rocketgram.AioHttpExecutor.run(bot,
                                       os.environ['WEBHOOK_URL'].strip(),
                                       os.environ.get('WEBHOOK_PATH', '/').strip(),
                                       host='0.0.0.0', port=port,
                                       drop_pending_updates=bool(int(os.environ.get('DROP_UPDATES', 0))),
                                       webhook_remove=not mode == 'heroku')
    logger.info('Bye!')


if __name__ == '__main__':
    main()
