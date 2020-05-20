from telegram.ext import BaseFilter
import manage
from howru_models.models import Patient
from log.logger import logger


class IsAnsweringFilter(BaseFilter):
    def filter(self, message):
        """
        Checks if the patient is answering a question
        :return: True if a question is being answered, False otherwise
        """
        patient = Patient.objects.get(identifier=message.from_user.id)
        return patient.pendingquestion_set.all().filter(answering=True)

# Initialize the class.
is_answering_filter = IsAnsweringFilter()