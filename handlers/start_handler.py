from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from config.messages import messages
from handlers import send_typing_action
from jobs.PendingQuestionJob import PendingQuestionJob
from log.logger import logger
import keyboards
import manage
from django.contrib.auth.models import User
from howru_models.models import Patient ,PendingQuestion
from howru_helpers import Flag

GENDER, PICTURE, LANGUAGE, SCHEDULE = range(4)


@send_typing_action
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


@send_typing_action
def language(update, context):
    language = update.message.text
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} chose language {language}')
    context.user_data['patient'].language = Flag.unflag(language)
    update.message.reply_text(text=messages[patient.language]['choose_gender'],
                              reply_markup=keyboards.gender_keyboard[patient.language])
    return GENDER


@send_typing_action
def gender(update, context):
    patient = context.user_data['patient']
    logger.info(
        f'User {update.message.from_user.username} id {update.message.from_user.id} chose gender {update.message.text}')
    update.message.reply_text(messages[patient.language]['choose_pic'], reply_markup=ReplyKeyboardRemove())
    patient.gender = update.message.text
    return PICTURE


@send_typing_action
def picture(update, context):
    patient = context.user_data['patient']
    photo_file = update.message.photo[-1].get_file()
    pic_name = f'pics/{update.message.from_user.id}..jpg'
    photo_file.download(pic_name)
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} sent picture {pic_name}')
    update.message.reply_text(messages[patient.language]['choose_schedule'])
    patient.picture = pic_name
    return SCHEDULE


@send_typing_action
def skip_picture(update, context):
    patient = context.user_data['patient']
    logger.info(
        f'User {update.message.from_user.username} id {update.message.from_user.id} did not send a picture, using default')
    patient.picture = f'pics/default_profile_picture.png'
    update.message.reply_text(messages[patient.language]['choose_schedule'])
    return SCHEDULE


@send_typing_action
def schedule(update, context):
    schedule = update.message.text
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} chose schedule {schedule}')
    patient.schedule = schedule
    return finish(update, context)


@send_typing_action
def finish(update, context):
    patient = context.user_data['patient']
    patient.save()
    # Add data analyst to all patients and assigned_to_all questions
    try:
        data_analyst = User.objects.get(username="data_analyst").doctor
        patient.assigned_doctors.add(data_analyst)
        patient.save()
        assigned_to_all = data_analyst.assigned_questions.filter(assigned_to_all=True)
        for question in assigned_to_all:
            pending_question = PendingQuestion(doctor=data_analyst,
                                               question=question,
                                               patient=patient,
                                               answering=False)
            pending_question.save()
        logger.info("Patient %s assigned to data_analyst", patient.username)
    except User.DoesNotExist:
        logger.error("data_analyst doctor does not exists")
    except:
        logger.exception("Exception adding patient %s to data_analyst.", patient.username)
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
