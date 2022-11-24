import os
from telegram import Update
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, ChatMemberHandler

import func
import shared
from log import logger


class NewChatMemberHandler(ChatMemberHandler):
    def __init__(self, callback, **kwargs):
        super().__init__(callback, chat_member_types=ChatMemberHandler.CHAT_MEMBER, **kwargs)

    def check_update(self, update: Update):
        if super().check_update(update):
            return update.chat_member.new_chat_member and update.chat_member.new_chat_member.status == 'member'


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
    shared.bot = updater.bot
    dp = updater.dispatcher
    dp.add_handler(NewChatMemberHandler(func.auto_kick_out))
    dp.add_handler(
        MessageHandler(Filters.status_update.chat_created & ~Filters.chat_type.channel, func.notify_monitoring))
    dp.add_handler(MessageHandler(Filters.is_automatic_forward, func.auto_poll))
    dp.add_handler(CommandHandler('set_poll', func.set_poll))
    dp.add_handler(CommandHandler('force_poll', func.force_poll))
    dp.add_handler(MessageHandler(Filters.chat_type.private, func.get_help))
    dp.add_handler(CommandHandler('help', func.get_help))

    updater.start_polling(allowed_updates=shared.ALLOWED_UPDATES)
    updater.idle()
