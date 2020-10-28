from datetime import datetime

from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler, MessageHandler, Filters

from chatbot.filters.IsAnsweringFilter import is_answering_filter
from chatbot.handlers import send_typing_action
from howru_models.models import AnsweredQuestion, PendingQuestion
from chatbot.log.logger import logger
import pytz


@send_typing_action
def answer_question(update, context):
    """
    Prompts user's question by querying PendingQuestion DB.
    Creates an AsweredQuestion object.
    """
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
    logger.info(f'User {user.username} id {user.id} answered "{response}" to question "{question_task.question}"')
    response_object = question_task.question.response_set.get(text=response)
    # Create answered question entry
    answered_question = AnsweredQuestion(patient_id=user.id, doctor=question_task.doctor,
                                         answer_date=datetime.now(pytz.timezone('Europe/Madrid')),
                                         response=response_object,
                                         question=question_task.question)
    answered_question.save()
    # Set answering to false
    question_task.answering = False
    question_task.save()

    return ConversationHandler.END


def _get_pending_question_task(user_id):
    """
    Obtains the question that the user is answering
    """
    return PendingQuestion.objects.get(patient_id=user_id, answering=True)


question_handler = ConversationHandler(
    entry_points=[MessageHandler(~Filters.command & is_answering_filter, answer_question)],
    states={},
    fallbacks=[],
    name="questions_handler"
)
