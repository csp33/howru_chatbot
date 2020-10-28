import time
from datetime import datetime, timedelta

from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler

import chatbot.keyboards as keyboards
from chatbot.config.messages import messages
import manage
from howru_models.models import *
from chatbot.log.logger import logger


def was_configurator_running(patient_id, context):
    """
    Returns wether the user had the configurator opened when questions were popped.
    """
    all_hand = context.dispatcher.handlers
    for dict_group in all_hand:
        for handler in all_hand[dict_group]:
            if isinstance(handler, ConversationHandler) and handler.name == "configurator" and str(
                    list(handler.conversations)[0][0]) == patient_id:
                return True
    return False


class PendingQuestionJob(object):
    def __init__(self, context, patient):
        self.patient = patient
        self._create_job(context)

    def job_callback(self, context):
        """
        Prompts PendingQuestions to the user.
        """
        pending_questions = self._get_pending_questions()
        for task in pending_questions:
            if not self.is_question_answered(task):
                question = task.question
                task.answering = True
                task.save()
                context.bot.send_message(chat_id=self.patient.identifier, text=question.text,
                                         reply_markup=keyboards.get_custom_keyboard(question.response_set.all()))
                while not self.is_question_answered(task):
                    time.sleep(0.5)
        message = messages[self.patient.language]['finish_answering'] if self.answered_questions_today() else \
            messages[self.patient.language]['no_questions']
        logger.info(f'User {self.patient.username} answered all the questions')
        context.bot.send_message(chat_id=self.patient.identifier, text=message, reply_markup=ReplyKeyboardRemove())
        time.sleep(0.1)
        if was_configurator_running(self.patient.identifier, context):
            logger.info(f'Reopening configurator for user {self.patient.username} id {self.patient.identifier}')
            context.bot.send_message(chat_id=self.patient.identifier,
                                     text=messages[self.patient.language]['select_config'],
                                     reply_markup=keyboards.config_keyboard[self.patient.language])

    def _create_job(self, context):
        context.job_queue.run_daily(callback=self.job_callback,
                                    time=self.patient.schedule,
                                    name=f'{self.patient.identifier}_pending_questions_job')

    @staticmethod
    def is_question_answered(question_task):
        """
        Returns wether the user answered the question today.
        :param question_task (PendingQuestion)
        """
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)
        tomorrow = today + timedelta(days=1)
        return AnsweredQuestion.objects.filter(question=question_task.question,
                                               patient=question_task.patient,
                                               answer_date__gt=today,
                                               answer_date__lt=tomorrow)

    def _get_pending_questions(self):
        """
        Builds a list of pending questions based on their frequency.
        """
        pending_questions = list()
        for pending_question in PendingQuestion.objects.filter(patient=self.patient).order_by("question__priority"):
            answered = AnsweredQuestion.objects.filter(question=pending_question.question,
                                                       patient=pending_question.patient).order_by("-answer_date")
            if not answered:
                # If the question has never been answered, add it to the queue
                pending_questions.append(pending_question)
            else:
                # As only_once questions are only added in the first if, they won't be added again
                last_answer_date = answered[0].answer_date
                now = datetime.now()
                today = datetime(now.year, now.month, now.day)
                if pending_question.question.frequency == "D" and last_answer_date.day < today.day:
                    # Daily
                    pending_questions.append(pending_question)
                if pending_question.question.frequency == "W" and last_answer_date.weekday == today.weekday:
                    # Weekly
                    pending_questions.append(pending_question)
                elif pending_question.question.frequency == "M" and last_answer_date.month < today.month \
                        and last_answer_date.day == today.day:
                    # Monthly
                    pending_questions.append(pending_question)
        return pending_questions

    @staticmethod
    def answered_questions_today():
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)
        tomorrow = today + timedelta(days=1)
        return AnsweredQuestion.objects.filter(answer_date__gt=today,
                                               answer_date__lt=tomorrow)
