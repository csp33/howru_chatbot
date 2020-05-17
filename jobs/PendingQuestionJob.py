import time
from datetime import datetime, timedelta

from telegram import ReplyKeyboardRemove

from config.messages import messages
from howru_helpers.MongoHelper import MongoHelper
from log.logger import logger
import manage
import keyboards
from howru_models.models import *


class PendingQuestionJob(object):
    def __init__(self, context, patient_id):
        try:
            self.patient = Patient.objects.get(identifier=patient_id)
        except:
            logger.exception("Patient %s does not exist in DB", patient_id)
        self._create_job(context)

    def job_callback(self, context):
        pending_questions = self._get_pending_questions()
        for task in pending_questions:
            if not self.is_question_answered(task):
                question = Question.objects.get(identifier=task.question_id)
                question.answering = True
                question.save()
                context.bot.send_message(chat_id=self.patient.identifier, text=question.text,
                                         reply_markup=keyboards.get_custom_keyboard(question.responses))
                while not self.is_question_answered(task):
                    time.sleep(0.5)
        message = messages[self.patient.language]['finish_answering'] if self.answered_questions_today() else \
            messages[self.patient.language]['no_questions']
        logger.info(f'User {self.patient.username} id {self.patient.identifier} answered all the questions')
        context.bot.send_message(chat_id=self.patient.identifier, text=message,
                                 reply_markup=ReplyKeyboardRemove())

    def _create_job(self, context):
        context.job_queue.run_daily(callback=self.job_callback,
                                    time=self.patient.schedule,
                                    name=f'{self.patient.identifier}_pending_questions_job')
        # TODO store jobs using pickle https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#save-and-load-jobs-using-pickle

    def is_question_answered(self, question_task):
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)
        tomorrow = today + timedelta(days=1)
        return AnsweredQuestion.objects.filter(question_id=question_task.question_id,
                                               patient_id = question_task.patient_id,
                                               answer_date__gt=today,
                                               answer_date__lt=tomorrow)

    def _get_pending_questions(self):
        return PendingQuestion.objects.filter(patient_id=self.patient.identifier)

    def answered_questions_today(self):
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)
        tomorrow = today + timedelta(days=1)
        return AnsweredQuestion.objects.filter(answer_date__gt=today,
                                               answer_date__lt=tomorrow)
