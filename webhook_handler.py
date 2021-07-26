import json
import telegram
import os

from log import logger
import func

TELEGRAM = 777000

TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    raise EnvironmentError('Telegram token is NOT SET!')

bot = telegram.Bot(TOKEN)
logger.info('Initialized.')


def dispatch(data):
    update = telegram.Update.de_json(json.loads(data), bot)
    message = update.message
    logger.debug(f'Received: {message}')

    if not message:
        logger.info('Nothing should do.')
        return

    if message.new_chat_members:
        func.auto_kick_out(update, bot_self_id=bot.id)
    elif message.from_user.id == TELEGRAM:
        func.auto_poll(update)
    elif message.text and message.text.startswith('/set_poll'):
        func.set_poll(update)
    elif message.chat.type == 'private' or message.text == '/help':
        func.get_help(update)
    else:
        logger.info('Nothing should do.')


def set_webhook(url):
    webhook = bot.set_webhook(url)
    return webhook
