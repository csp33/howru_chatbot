from datetime import datetime

from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler, MessageHandler, Filters

from howru_models.models import AnsweredQuestion, PendingQuestion
from log.logger import logger

ANSWERING, ANSWERED = range(2)


# noinspection PyUnresolvedReferences
class QuestionHandler(object):
    def answer_question(self, update, context):
        user = update.message.from_user
        response = update.message.text
        # Get question that is being answered from DB:
        question_task = self._get_pending_question_task(str(user.id))
        if question_task:
            logger.debug(
                f'User {user.username} id {user.id} answered {response} to question {question_task["question_id"]} task {question_task["_id"]}')
            # Create answered question entry
            answered_question = AnsweredQuestion(patient_id=user.id, doctor_id=question_task.doctor_id,
                                                 answer_date=datetime.utcnow(), response=response,
                                                 question_id=question_task.question_id)
            answered_question.save()
            # Set answering to false
            question_task.answering = True
            question_task.save()

        else:
            logger.debug(
                f'User {user.username} id {user.id} wrote {response} while there was no question to answer')
            update.message.reply_text("Unrecognized command\nComando no reconocido", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    @staticmethod
    def _get_pending_question_task(user_id):
        return PendingQuestion.objects.get(patient_id=user_id)


instance = QuestionHandler()
question_handler = ConversationHandler(
    entry_points=[MessageHandler(~Filters.regex('^/...$'), instance.answer_question)],
    states={},
    fallbacks=[]
)
