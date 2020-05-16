from functools import wraps

from telegram import ChatAction

from log.logger import logger


def error_callback(update, context):
    logger.exception(
        f'Error {context.error} while performing update on user {update.message.from_user.username} id {update.message.from_user.id}')


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(update, context, *args, **kwargs)

        return command_func

    return decorator


send_typing_action = send_action(ChatAction.TYPING)
send_upload_photo_action = send_action(ChatAction.UPLOAD_PHOTO)
