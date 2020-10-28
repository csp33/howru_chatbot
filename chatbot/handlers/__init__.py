from functools import wraps
import traceback
from telegram import ChatAction

from chatbot.log.logger import logger
from chatbot.config.bot_config import ADMINS_CHAT_IDS

def error_callback(update, context):
    e = context.error
    try:
        user = update.message.from_user.username
    except Exception:
        user = ""
    for admin_id in ADMINS_CHAT_IDS:
        context.bot.send_message(chat_id=admin_id, text=f'Exception {str(e)} when performing update on user {user}')
        context.bot.send_message(chat_id=admin_id, text=''.join(traceback.format_tb(e.__traceback__)))
    logger.exception(f'Error {e} while performing update on user {user}')


def send_action(action):
    """
    Sends `action` while processing func command.
    https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#send-action-while-handling-command-decorator
    """

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


send_typing_action = send_action(ChatAction.TYPING)
send_upload_photo_action = send_action(ChatAction.UPLOAD_PHOTO)
