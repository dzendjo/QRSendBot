from j2tools import YamlLoader
from jinja2 import Environment
from tools import to_t, to_k
from contextvars import ContextVar
import os

jinja = Environment(loader=YamlLoader('templates/ru.yml'))
jinja.filters['to_t'] = to_t
jinja.filters['to_k'] = to_k

admins = [788886288, 2519539, 791380027]

api_server = None
api_server_host = 'localhost'
api_server_port = 8081
bot = None
bot_name = 'TG_BOT'

NATS_SERVER_URI = os.environ.get('NATS_SERVER_URI','127.0.0.1:4222')
NATS_TOKEN = os.environ.get('NATS_TOKEN','')

nc = None

current_T = ContextVar('current_T')
get_t = None

current_user = ContextVar('current_user')

ad_token = 'cc71c7d77fd766782e0025a6186756ec'
api_url_available_campaigns = 'https://addpromoapi.fastbots.net/available-adverts'
api_url_get_advert = 'https://addpromoapi.fastbots.net/get-advert'