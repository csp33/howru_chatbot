from base64 import b64encode

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
# noinspection PyUnresolvedReferences
from django_better_admin_arrayfield.models.fields import ArrayField

from howru_helpers import UTCTime


class Response(models.Model):
    text = models.CharField(max_length=100)
    order = models.IntegerField(null=False)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    def __str__(self):
        return self.text

class Question(models.Model):
    text = models.CharField(max_length=100)
    creator = models.ForeignKey('Doctor', on_delete=models.CASCADE)
    public = models.BooleanField()
    language = models.CharField(choices=[("GB", "English"), ("ES", "Spanish")], max_length=2)
    assigned_to_all = models.BooleanField()
    frequency = models.CharField(
        choices=[("D", "Daily"), ("W", "Weekly"), ("M", "Monthly"), ("O", "Once")],
        max_length=1, default="D")
    priority = models.IntegerField(default=1)

    def __str__(self):
        return self.text


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    assigned_questions = models.ManyToManyField(Question, blank=True)
    is_analyst = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Doctor.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.doctor.save()


class Patient(models.Model):
    identifier = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(max_length=100, null=True)
    _picture = models.BinaryField(blank=True, db_column="picture")
    _gender = models.CharField(choices=[("M", "Male"), ("F", "Female"), ("O", "Other")], max_length=1,
                               db_column="gender", null=True)
    language = models.CharField(choices=[("GB", "English"), ("ES", "Spanish")], max_length=2)
    username = models.CharField(max_length=20, null=True)
    _schedule = models.DateTimeField(
        db_column="schedule"
    )
    assigned_doctors = models.ManyToManyField(Doctor, blank=True)

    def __str__(self):
        return self.username

    @property
    def picture(self):
        return b64encode(self._picture).decode('utf-8')

    @picture.setter
    def picture(self, value):
        self._picture = open(value, 'rb').read()

    @property
    def schedule(self):
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        utc_result = UTCTime.get_utc_result(value)
        self._schedule = utc_result

    @property
    def gender(self):
        GENDER_MAPPING = {
            "M": {"ES": "Masculino", "GB": "Male"},
            "F": {"ES": "Femenino", "GB": "Female"},
            "O": {"ES": "Otro", "GB": "Other"},
        }
        return GENDER_MAPPING[self._gender][self.language]

    @gender.setter
    def gender(self, value):
        if value in ["Masculino", "Male"]:
            gender = "M"
        elif value in ["Femenino", "Female"]:
            gender = "F"
        else:
            gender = "O"
        self._gender = gender


class JournalEntry(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def __str__(self):
        return "{} - {} - {}".format(self.question, self.patient, self.doctor)


class PendingQuestion(JournalEntry):
    answering = models.BooleanField()


class AnsweredQuestion(JournalEntry):
    answer_date = models.DateTimeField()
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    def __str__(self):
        base = str(super())
        return f'{base} - {self.response} - {self.answer_date}'
