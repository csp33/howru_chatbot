from telegram.ext.filters import InvertedFilter, MergedFilter
import manage
from howru_models.models import Patient
from chatbot.log.logger import logger


class IsAnsweringFilter:
    name = None
    update_filter = False
    data_filter = False

    def __call__(self, update):
        if self.update_filter:
            return self.filter(update)
        else:
            return self.filter(update.effective_message)

    def __and__(self, other):
        return MergedFilter(self, and_filter=other)

    def __or__(self, other):
        return MergedFilter(self, or_filter=other)

    def __invert__(self):
        return InvertedFilter(self)

    def __repr__(self):
        # We do this here instead of in a __init__ so filter don't have to call __init__ or super()
        if self.name is None:
            self.name = self.__class__.__name__
        return self.name

    def filter(self, message):
        """
        Checks if the patient is answering a question
        :return: True if a question is being answered, False otherwise
        """
        patient = Patient.objects.get(identifier=message.from_user.id)
        return patient.pendingquestion_set.all().filter(answering=True)

# Initialize the class.
is_answering_filter = IsAnsweringFilter()
