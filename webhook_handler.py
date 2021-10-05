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


def dispatch(update: telegram.Update):
    message = update.message
    if not message:
        logger.info('Not a message.')
        return
    text = message.text
    logger.debug(f'Received: {message}')
    if not message:
        logger.info('Nothing should do.')
        return
    if message.new_chat_members:
        func.auto_kick_out(update, bot_self_id=bot.id)
        return
    if message.group_chat_created:
        func.notify_monitoring(update)
        return
    if message.from_user.id == TELEGRAM:
        func.auto_poll(update)
        return
    if text and text.startswith('/'):
        command = text.split(' ')[0]
        if not (command.find('@') == -1 or command.endswith(bot.username)):
            logger.info("None of my business.")
            return
        if text.startswith('/set_poll'):
            func.set_poll(update)
            return
        if text.startswith('/force_poll'):
            func.force_poll(update)
            return
        if text.startswith('/help'):
            func.get_help(update)
            return
    if message.chat.type == 'private':
        func.get_help(update)
        return

    logger.info('Nothing should do.')


def webhook(data):
    update = telegram.Update.de_json(json.loads(data), bot)
    dispatch(update)


def set_webhook(url):
    return bot.set_webhook(url)
