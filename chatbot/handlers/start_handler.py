from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from chatbot.config.messages import messages
from chatbot.handlers import send_typing_action
from chatbot.log.logger import logger
import chatbot.keyboards as keyboards
import manage
from chatbot.jobs.PendingQuestionJob import PendingQuestionJob
from django.contrib.auth.models import User
from howru_models.models import Patient ,PendingQuestion, Doctor
from howru_helpers import Flag

GENDER, PICTURE, LANGUAGE, SCHEDULE = range(4)


@send_typing_action
def start(update, context):
    """
    Shows welcome message and asks for language
    """
    # Check that user is not registered
    try:
        patient = Patient.objects.get(identifier=update.message.from_user.id)
        logger.info(
            f'User {update.message.from_user.username} tried to register again.')
        update.message.reply_text(text=messages[patient.language]['already_exists'])
        return ConversationHandler.END
    except Patient.DoesNotExist:
        # The user should not exist in DB
        context.user_data['patient'] = Patient(name=update.message.from_user.first_name,
                                               identifier=str(update.message.from_user.id),
                                               username=update.message.from_user.username)

    logger.info(f'User {update.message.from_user.username} started a new conversation')
    update.message.reply_text(text=f'Hi {update.message.from_user.first_name}. Welcome to HOW-R-U psychologist bot.\n'
                                   f'Hola {update.message.from_user.first_name}. Bienvenido al bot psicólogo HOW-R-U')
    update.message.reply_text(text=f'Please select a language:\nElija un idioma por favor:',
                              reply_markup=keyboards.language_keyboard)

    return LANGUAGE


@send_typing_action
def language(update, context):
    """
    Processes language and asks for gender
    """
    language = update.message.text
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} chose language {language}')
    context.user_data['patient'].language = Flag.unflag(language)
    update.message.reply_text(text=messages[patient.language]['choose_gender'],
                              reply_markup=keyboards.gender_keyboard[patient.language])
    return GENDER


@send_typing_action
def gender(update, context):
    """
    Processes gender and asks for picture
    """
    patient = context.user_data['patient']
    logger.info(
        f'User {update.message.from_user.username} chose gender {update.message.text}')
    update.message.reply_text(messages[patient.language]['choose_pic'], reply_markup=ReplyKeyboardRemove())
    patient.gender = update.message.text
    return PICTURE


@send_typing_action
def picture(update, context):
    """
    Processes picture and asks for schedule
    """
    patient = context.user_data['patient']
    photo_file = update.message.photo[-1].get_file()
    pic_name = f'/opt/chatbot/chatbot/pics/{update.message.from_user.id}.jpg'
    photo_file.download(pic_name)
    logger.info(f'User {update.message.from_user.username} sent picture {pic_name}')
    update.message.reply_text(messages[patient.language]['choose_schedule'])
    patient.picture = pic_name
    return SCHEDULE


@send_typing_action
def skip_picture(update, context):
    """
    Sets default picture and asks for schedule
    """
    patient = context.user_data['patient']
    logger.info(
        f'User {update.message.from_user.username} did not send a picture, using default')
    patient.picture = '/opt/chatbot/chatbot/pics/default_profile_picture.png'
    update.message.reply_text(messages[patient.language]['choose_schedule'])
    return SCHEDULE


@send_typing_action
def schedule(update, context):
    """
    Processes schedule and calls finish() method
    """
    schedule = update.message.text
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} chose schedule {schedule}')
    patient.schedule = schedule
    return finish(update, context)


@send_typing_action
def finish(update, context):
    """
    Saves patient in DB, assigns him/her to data_analyst, creates PendingQuestion entries for assigned_to_all questions
    and finally creates the user's PendingQuestionJob
    """
    patient = context.user_data['patient']
    patient.save()
    # Add patient to data analysts and assigned_to_all questions
    try:
        data_analysts = Doctor.objects.filter(is_analyst=True)
        for doctor in data_analysts:
            patient.assigned_doctors.add(doctor)
            patient.save()
            assigned_to_all = doctor.assigned_questions.filter(assigned_to_all=True)
            for question in assigned_to_all:
                pending_question = PendingQuestion(doctor=doctor,
                                                   question=question,
                                                   patient=patient,
                                                   answering=False)
                pending_question.save()
        logger.info("Patient %s assigned to data_analysts", patient.username)
    except:
        logger.exception("Exception while adding patient %s to data_analysts.", patient.username)
    update.message.reply_text(messages[patient.language]['registration_ok'])
    logger.info(f'Creating pending_questions job for user {update.message.from_user.username}')
    PendingQuestionJob(context, patient)
    return ConversationHandler.END


start_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        LANGUAGE: [MessageHandler(Filters.regex(f'^({Flag.flag("es")}|{Flag.flag("gb")})$'), language)],
        GENDER: [MessageHandler(Filters.regex('^(Male|Female|Other|Masculino|Femenino|Otro)$'), gender)],
        PICTURE: [MessageHandler(Filters.photo, picture), CommandHandler('skip', skip_picture)],
        SCHEDULE: [MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), schedule)]
    },
    fallbacks=[],
    name="starter"
)
