from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from config.messages import messages
from jobs.PendingQuestionJob import PendingQuestionJob
from log.logger import logger
import keyboards
import manage
from howru_models.models import Patient
from howru_helpers import Flag

GENDER, PICTURE, LANGUAGE, SCHEDULE = range(4)


def start(update, context):
    # Check that user is not registered
    try:
        patient = Patient.objects.get(identifier=update.message.from_user.id)
        logger.info(
            f'User {update.message.from_user.username} id {update.message.from_user.id} tried to register again.')
        update.message.reply_text(text=messages[patient.language]['already_exists'])
        return ConversationHandler.END
    except Patient.DoesNotExist:
        # If the user should not exist in DB
        context.user_data['patient'] = Patient(name=update.message.from_user.first_name,
                                               identifier=str(update.message.from_user.id),
                                               username=update.message.from_user.username)

    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} started a new conversation')
    update.message.reply_text(text=f'Hi {update.message.from_user.first_name}. Welcome to HOW-R-U psychologist bot.\n'
                                   f'Hola {update.message.from_user.first_name}. Bienvenido al bot psicólogo HOW-R-U')
    update.message.reply_text(text=f'Please select a language:\nElija un idioma por favor:',
                              reply_markup=keyboards.language_keyboard)

    return LANGUAGE


def language(update, context):
    language = update.message.text
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} chose language {language}')
    context.user_data['patient'].language = Flag.unflag(language)
    update.message.reply_text(text=messages[patient.language]['choose_gender'],
                              reply_markup=keyboards.gender_keyboard[patient.language])
    return GENDER


def gender(update, context):
    patient = context.user_data['patient']
    logger.info(
        f'User {update.message.from_user.username} id {update.message.from_user.id} chose gender {update.message.text}')
    update.message.reply_text(messages[patient.language]['choose_pic'], reply_markup=ReplyKeyboardRemove())
    patient.gender = update.message.text
    return PICTURE


def picture(update, context):
    patient = context.user_data['patient']
    photo_file = update.message.photo[-1].get_file()
    pic_name = f'pics/{update.message.from_user.id}..jpg'
    photo_file.download(pic_name)
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} sent picture {pic_name}')
    update.message.reply_text(messages[patient.language]['choose_schedule'])
    patient.picture = pic_name
    return SCHEDULE


def skip_picture(update, context):
    patient = context.user_data['patient']
    logger.info(
        f'User {update.message.from_user.username} id {update.message.from_user.id} did not send a picture, using default')
    patient.picture = f'pics/default_profile_picture.png'
    update.message.reply_text(messages[patient.language]['choose_schedule'])
    return SCHEDULE


def schedule(update, context):
    schedule = update.message.text
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} chose schedule {schedule}')
    patient.schedule = schedule
    return finish(update, context)


def finish(update, context):
    patient = context.user_data['patient']
    patient.save()
    update.message.reply_text(messages[patient.language]['registration_ok'])
    logger.info(f'Creating pending_questions job for user {update.message.from_user.username}')
    PendingQuestionJob(context, patient.identifier)
    return ConversationHandler.END


start_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        LANGUAGE: [MessageHandler(Filters.regex(f'^({Flag.flag("es")}|{Flag.flag("gb")})$'),language)],
        GENDER: [MessageHandler(Filters.regex('^(Male|Female|Other|Masculino|Femenino|Otro)$'), gender)],
        PICTURE: [MessageHandler(Filters.photo, picture), CommandHandler('skip', skip_picture)],
        SCHEDULE: [MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), schedule)]
    },
    fallbacks=[]
)
