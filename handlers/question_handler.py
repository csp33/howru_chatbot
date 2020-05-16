from datetime import datetime

from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler, MessageHandler, Filters

from howru_helpers.MongoHelper import MongoHelper
from log.logger import logger
from howru_models.Journal.AnsweredQuestion import AnsweredQuestion

ANSWERING, ANSWERED = range(2)


class QuestionHandler(object):
    def __init__(self):
        self.pending_db = MongoHelper(db='journal', collection='pending_questions')
        self.answered_db = MongoHelper(db='journal', collection='answered_questions')

    def answer_question(self, update, context):
        user = update.message.from_user
        response = update.message.text
        # Get question that is being answered from DB:
        question_task = self._get_pending_question_task(str(user.id))
        if question_task:
            logger.debug(
                f'User {user.username} id {user.id} answered {response} to question {question_task["question_id"]} task {question_task["_id"]}')
            # Create answered question entry
            answered_question = AnsweredQuestion(patient_id=user.id, doctor_id=question_task['doctor_id'],
                                                 answer_date=datetime.utcnow(), response=response,
                                                 question_id=question_task['question_id'])
            answered_question.to_db()
            # Set answering to false
            self.pending_db.update_document(question_task['_id'], {'$set': {'answering': False}})
            #logger.debug(f'Deleting question task {question_task["_id"]} from pending_db...')
            #self.pending_db.delete_document_by_id(question_task['_id'])
        else:
            logger.debug(
                f'User {user.username} id {user.id} wrote {response} while there was no question to answer')
            update.message.reply_text("Unrecognized command\nComando no reconocido", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    def _get_pending_question_task(self, user_id):
        return self.pending_db.search_one({
            'patient_id': user_id,
            'answering': True
        })


instance = QuestionHandler()
question_handler = ConversationHandler(
    entry_points=[MessageHandler(~Filters.regex('^/...$'), instance.answer_question)],
    states={},
    fallbacks=[]
)
