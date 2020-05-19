from datetime import datetime

from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler, MessageHandler, Filters

from howru_models.models import AnsweredQuestion, PendingQuestion
from log.logger import logger
import pytz

ANSWERING, ANSWERED = range(2)


def answer_question(update, context):
    user = update.message.from_user
    response = update.message.text
    # Get question that is being answered from DB:
    try:
        question_task = _get_pending_question_task(str(user.id))
    except PendingQuestion.DoesNotExist:
        logger.info(
            f'User {user.username} id {user.id} wrote {response} while there was no question to answer')
        update.message.reply_text("Unrecognized command\nComando no reconocido", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    """
    logger.info(
        f'User {user.username} id {user.id} answered {response} to question {question_task.id} '
        f'task {question_task["_id"]}')
    """
    # Create answered question entry
    answered_question = AnsweredQuestion(patient_id_id=user.id, doctor_id=question_task.doctor_id,
                                         answer_date=datetime.now(pytz.timezone('Europe/Madrid')),
                                         response=response,
                                         question_id=question_task.question_id)
    answered_question.save()
    # Set answering to false
    question_task.answering = False
    question_task.save()

    return ConversationHandler.END


def _get_pending_question_task(user_id):
    return PendingQuestion.objects.get(patient_id=user_id, answering=True)


question_handler = ConversationHandler(
    entry_points=[MessageHandler(~Filters.regex('^/...$'), answer_question)],
    states={},
    fallbacks=[]
)
