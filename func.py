import functools
import os
from datetime import datetime, timedelta, timezone

import telegram
import shared
from telegram.error import BadRequest

from log import logger

GROUP = 1087968824
RDS_NAME = 'comments-helper-bot'
DEFAULT_POLL_OPTIONS = ['⭕️', '🌱', '🤔', '🕊', '💊']
DEFAULT_POLL_QUESTION = '💭'
last_media_group_id = None

rds = None
REDIS_HOST = os.environ.get('REDIS_HOST')
if REDIS_HOST:
    try:
        import redis

        REDIS_PORT = os.environ.get('REDIS_PORT')
        REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
        rds = redis.Redis(host=REDIS_HOST,
                          port=REDIS_PORT if REDIS_PORT else 6379,
                          password=REDIS_PASSWORD if REDIS_PASSWORD else None,
                          socket_connect_timeout=1.5,
                          socket_timeout=1.5,
                          retry_on_timeout=True,
                          decode_responses=True)

        _ = rds.type(RDS_NAME)
        if _ != 'hash' and _ != 'none':
            rds.delete(RDS_NAME)
    except Exception as _e:
        logger.error('Cannot connect to redis, run in non-redis mode.', exc_info=_e)


def permission_required(disallow_in_private):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(update, context=None, *args, **kwargs):
            message = update.message
            command = message.text
            user_id = update.effective_user.id
            if message.chat.type not in ('supergroup', 'group'):
                if disallow_in_private:
                    update.effective_message.reply_text('This command can only be used in a discussion group.')
                    logger.info(f'Refused {user_id} to use {command} in non-group chat.')
                    return
                logger.info(f'Allowed {user_id} to use {command} in non-group chat.')
                return function(update, context, *args, **kwargs)

            user_status = update.effective_chat.get_member(user_id).status
            if user_id != GROUP and user_status not in ('administrator', 'creator'):
                update.effective_message.reply_text('This command can only be used by an administrator.')
                logger.info(
                    f'Refused {user_id} ({user_status}) to use {command} in {message.chat.title} ({message.chat.id}).')
                return
            logger.info(
                f'Allowed {user_id} ({user_status}) to use {command} in {message.chat.title} ({message.chat.id}).')
            return function(update, context, *args, **kwargs)

        return wrapper

    return decorator


@permission_required(disallow_in_private=False)
def get_help(update: telegram.Update, context=None):
    message = update.message
    update.effective_message.reply_text(
        'Add me to the *discussion group* of your channel\\. '
        'I will automatically attach a poll to each channel message in the group\\.\n'
        'Reply /force\\_poll to a message to manually attach a poll '
        '\\(the command message will be automatically deleted if granted "Delete message" permission\\)\\.\n'
        'I can also automatically remove \\(and ban for 60s\\) any user attempting to join the group '
        'if granted "Ban users" permission\\.'
        +
        ('\n\nYou can customize polls by sending /set\\_poll\\.' if rds else ''),
        parse_mode='MarkdownV2')
    logger.info(f'Replied help message to {message.chat.title} ({message.chat.id}).')


@permission_required(disallow_in_private=True)
def set_poll(update: telegram.Update, context=None, disposable=False):
    message = update.message
    reply = update.effective_message.reply_text
    if not rds:
        reply('This bot does not support poll customization or currently cannot connect to the database.')
        logger.info(f'Replied "currently cannot set poll" message.')
        return

    command = message.text
    if command.endswith('<%MANUAL%>'):
        if disposable:
            return
        logger.info(f'Disabled auto poll.')
        try:
            rds.hset(RDS_NAME, message.chat.id, '<%MANUAL%>')
        except Exception as e:
            reply('Database error.')
            logger.error(f'Database error!', exc_info=e)
            return
        reply('Disabled auto poll\\. You must reply /force\\_poll to a message to manually attach a poll\\.\n\n'
              'To re\\-enable auto poll, send `/set_poll <%DEFAULT%>`\\.', parse_mode='MarkdownV2')
        return
    if command.endswith('<%DEFAULT%>'):
        if disposable:
            poll(update, reply_to_message_id=message.reply_to_message.message_id,
                 options_list=[DEFAULT_POLL_QUESTION, *DEFAULT_POLL_OPTIONS])
            return
        logger.info(f'Reset poll settings.')
        try:
            rds.hdel(RDS_NAME, message.chat.id)
        except Exception as e:
            reply('Database error.')
            logger.error(f'Database error!', exc_info=e)
            return
        poll(update)
        return
    if command.find(' ') != -1:
        if command.find('<%%>') != -1:
            arguments = command.split(' ', 1)[1].split('<%%>')
        else:
            arguments = command.split(' ')[1:]
        if 3 <= len(arguments) <= 11:
            if disposable:
                poll(update, reply_to_message_id=message.reply_to_message.message_id,
                     options_list=[arguments[0][:299], *(option[:99] for option in arguments[1:])])
                return
            logger.info(f'Set poll settings.')
            settings = f'{arguments[0][:299]}<%%>{"<%%>".join(option[:99] for option in arguments[1:])}'
            try:
                rds.hset(RDS_NAME, message.chat.id, settings)
            except Exception as e:
                reply('Database error.')
                logger.error(f'Database error!', exc_info=e)
                return
            poll(update)
            return
        reply('Invalid arguments!')
        logger.info(f'Invalid arguments.')
        return

    replied_help_message = reply(
        '*\\[Command usage\\]*\n'
        'The 1st argument is the title, and the rest are the options\\.\n\n'
        'If the title or options contains spaces, separate them with `<%%>`:\n'
        '`/set_poll Title<%%>Option 1<%%>Option 2<%%>Option 3`\n\n'
        'If the title and options do not contain spaces, separate them with spaces:\n'
        '`/set_poll 💬 1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟`\n\n'
        '*The title must be 1\\-300 characters long, '
        'and there must be 2\\-10 options with 1\\-100 characters each\\.*\n\n'
        'Disable auto poll is possible, just send `/set_poll <%MANUAL%>`\\.\n'
        'If you would like to reset default, send `/set_poll <%DEFAULT%>`\\.\n\n'
        'Your current setting is \\(if nothing, your group is in manual mode\\):',
        parse_mode='MarkdownV2')
    poll(update, reply_to_message_id=replied_help_message.message_id)
    logger.info(f'Replied /set_poll help message.')


@permission_required(disallow_in_private=True)
def force_poll(update: telegram.Update, context=None):
    message = update.message
    if not message.reply_to_message:
        update.effective_message.reply_text(
            'Reply this command to the message that needs to be attached with a poll\\.\n\n'
            'According to your settings:\n'
            '`/force_poll`\n\n'
            'Or temporarily use the different settings:\n'
            '`/force_poll Title<%%>Option 1<%%>Option 2<%%>Option 3`\n'
            '`/force_poll 💬 1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟`\n\n'
            'Grant me "Delete messages" permission and I will automatically delete the command message\\.',
            parse_mode='MarkdownV2')
        logger.info(f'Replied /force_poll help message.')
        return
    if message.text.find(' ') != -1:
        set_poll(update, disposable=True)
        return
    reply_to_message_id = message.reply_to_message.message_id
    poll(update, reply_to_message_id=reply_to_message_id, manual=True)
    try:
        message.delete()
    except:
        pass


def notify_monitoring(update: telegram.Update, context=None):
    message = update.message
    update.effective_message.reply_text(
        f'Start monitoring this group. Group name: {message.chat.title}\n\n'
        'Manually attach a poll by replying /force_poll to a message.\n'
        'Grant me "Ban users" permission if you would like me to automatically remove (and ban for 60s) '
        'any user attempting to join this group.'
        +
        ('\n\nYou can customize polls by sending /set_poll.' if rds else ''),
        quote=False
    )
    logger.info(f'Start monitoring {message.chat.title} ({message.chat.id}).')


def auto_kick_out(update: telegram.Update, context=None, bot_self_id=None):
    message = update.message
    if context and not bot_self_id:
        bot_self_id = context.bot.bot.id
    for new_chat_member in message.new_chat_members:
        user_id = new_chat_member.id
        if bot_self_id == user_id:
            notify_monitoring(update)
            continue
        if bot_self_id and not update.effective_chat.get_member(bot_self_id).can_restrict_members:
            logger.info(f'No permission, skipped auto removed {user_id} in {message.chat.title} ({message.chat.id}).')
            return
        try:
            update.effective_chat.ban_member(user_id, until_date=datetime.now(timezone.utc) + timedelta(seconds=60))
        except BadRequest as e:
            logger.info(f'{e}. Cannot remove {user_id} from {message.chat.title} ({message.chat.id}).')
            continue
        logger.info(f'Removed {user_id} from {message.chat.title} ({message.chat.id}).')


def auto_poll(update: telegram.Update, context=None):
    global last_media_group_id
    message = update.message
    if (message.forward_from_chat is None and message.forward_from is None) \
            or message.sender_chat.id != shared.bot.get_chat(update.effective_chat.id).linked_chat_id:
        # message from a user-hides-behind channel will not have `forward_from_chat`
        # (except they forward a channel message, we should verify `sender_chat.id`)
        # However, forwarded-from-user message from linked channel will not have `forward_from_chat` but `forward_from`
        logger.debug(f'Ignored auto poll from an unrelated channel {message.sender_chat.id}'
                     f'in {message.chat.title} ({message.chat.id}).')
        return
    media_group_id = message.media_group_id
    logger.info(f'Last media group id: {str(last_media_group_id)}')
    if media_group_id is not None:
        if media_group_id == last_media_group_id:
            logger.info(f'Skipped rest medium message from the same album.')
            return
        last_media_group_id = media_group_id

    poll(update)


def poll(update: telegram.Update, context=None, reply_to_message_id=None, options_list=None, manual=False):
    message = update.message
    question = DEFAULT_POLL_QUESTION
    options = DEFAULT_POLL_OPTIONS
    if options_list:
        question = options_list[0]
        options = options_list[1:]
    elif rds:
        try:
            options_str = rds.hget(RDS_NAME, message.chat.id)
            if options_str:
                if options_str == '<%MANUAL%>':
                    if not manual:
                        logger.info('Skipped poll because the group has disabled auto poll.')
                        return
                else:
                    options_list = options_str.split('<%%>')
                    question = options_list[0]
                    options = options_list[1:]
        except:
            question = DEFAULT_POLL_QUESTION
            options = DEFAULT_POLL_OPTIONS
    update.effective_message.reply_poll(question=question,
                                        options=options,
                                        reply_to_message_id=reply_to_message_id,
                                        disable_notification=True,
                                        quote=True
                                        )
    logger.info(f'Replied a poll to {message.message_id} in {message.chat.title} ({message.chat.id}).')
