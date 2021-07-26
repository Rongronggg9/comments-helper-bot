import os
from telegram.ext import Updater, MessageHandler, Filters

import func
from log import logger

TELEGRAM = 777000

if __name__ == '__main__':
    TOKEN = os.environ.get('TOKEN')
    if not TOKEN or TOKEN == 'X':
        raise EnvironmentError('Telegram token is NOT SET!')

    T_PROXY = os.environ.get('T_PROXY')
    if not T_PROXY or T_PROXY != 'X':
        telegram_proxy = T_PROXY
    else:
        telegram_proxy = ''

    logger.info('Bot is running.')

    updater = Updater(token=TOKEN, use_context=True, request_kwargs={'proxy_url': telegram_proxy})
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, func.auto_kick_out))
    dp.add_handler(
        MessageHandler(Filters.status_update.chat_created & ~Filters.chat_type.channel, func.notify_monitoring))
    dp.add_handler(MessageHandler(Filters.user(TELEGRAM), func.auto_poll))
    dp.add_handler(MessageHandler(Filters.regex(r'^/set_poll'), func.set_poll))
    dp.add_handler(MessageHandler(Filters.chat_type.private, func.get_help))
    dp.add_handler(MessageHandler(Filters.text('/help'), func.get_help))

    updater.start_polling()
    updater.idle()
