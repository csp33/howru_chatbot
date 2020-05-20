import base64
import os
from datetime import datetime

from telegram import ReplyKeyboardRemove, ParseMode
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, run_async

from config.messages import messages
from filters.IsAnsweringFilter import is_answering_filter
from howru_helpers import UTCTime, Flag
from jobs.PendingQuestionJob import PendingQuestionJob
from log.logger import logger
import keyboards
import manage
from howru_models.models import Patient

PROCESS_PROFILE_PIC, PROCESS_NAME, PROCESS_GENDER, CHOOSING, PROCESS_LANGUAGE, PROCESS_DELETE_USER, PROCESS_SCHEDULE = \
    range(7)


def config_menu(update, context):
    patient = context.user_data['patient']
    context.bot.send_message(chat_id=update.message.from_user.id,
                             text=messages[patient.language]['select_config'],
                             reply_markup=keyboards.config_keyboard[patient.language])
    return CHOOSING


def config(update, context):
    context.user_data['patient'] = Patient.objects.get(identifier=update.message.from_user.id)
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} started the configurator')
    try:
        context.user_data['patient'] = Patient.objects.get(identifier=update.message.from_user.id)
    except Exception:
        logger.info(
            f'User {update.message.from_user.username} id {update.message.from_user.id} tried to start the configurator but was not registered')
        update.message.reply_text('You must register first by clicking /start\n'
                                  'Debes registrarte primero pulsando /start.',
                                  reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    return config_menu(update, context)


def ask_profile_pic(update, context):
    patient = context.user_data['patient']
    # Send current picture
    update.message.reply_text(messages[patient.language]['current_picture'],
                              reply_markup=ReplyKeyboardRemove())
    with open('current_pic.png', 'wb') as output:
        output.write(base64.b64decode(patient.picture))
    update.message.reply_photo(open('current_pic.png', 'rb'))
    os.remove('current_pic.png')
    update.message.reply_text(messages[patient.language]['change_picture'], reply_markup=ReplyKeyboardRemove())
    return PROCESS_PROFILE_PIC


@run_async
def process_profile_pic(update, context):
    patient = context.user_data['patient']
    photo_file = update.message.photo[-1].get_file()
    pic_name = f'pics/{update.message.from_user.id}.jpg'
    photo_file.download(pic_name)
    patient.picture = pic_name
    patient.save()
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} changed profile picture')
    update.message.reply_text(messages[patient.language]['picture_updated'],
                              reply_markup=ReplyKeyboardRemove())
    return config_menu(update, context)


def ask_change_name(update, context):
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} asked to change name')
    update.message.reply_text(messages[patient.language]['current_name'] + patient.name)
    update.message.reply_text(messages[patient.language]['change_name'], reply_markup=ReplyKeyboardRemove())
    return PROCESS_NAME


@run_async
def process_name(update, context):
    patient = context.user_data['patient']
    old_name = patient.name
    name = update.message.text
    patient.name = name
    patient.save(())
    logger.info(
        f'User {update.message.from_user.username} old  name {old_name} id {update.message.from_user.id} changed name to {name}')
    update.message.reply_text(messages[patient.language]['name_updated'])
    return config_menu(update, context)


def ask_change_gender(update, context):
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} asked to change gender')
    update.message.reply_text(messages[patient.language]['current_gender'] + patient.gender)
    update.message.reply_text(messages[patient.language]['change_gender'],
                              reply_markup=keyboards.gender_keyboard[patient.language])
    return PROCESS_GENDER


@run_async
def process_gender(update, context):
    patient = context.user_data['patient']
    gender = update.message.text
    patient.gender = gender
    patient.save(())
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} changed gender to {gender}')
    update.message.reply_text(messages[patient.language]['gender_updated'])
    return config_menu(update, context)


def ask_change_language(update, context):
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} asked to change language')
    update.message.reply_text(messages[patient.language]['current_language'] + patient.language)
    update.message.reply_text(messages[patient.language]['change_language'],
                              reply_markup=keyboards.language_keyboard)
    return PROCESS_LANGUAGE


@run_async
def process_language(update, context):
    patient = context.user_data['patient']
    patient.language = Flag.unflag(update.message.text)
    patient.save()
    logger.info(
        f'User {update.message.from_user.username} id {update.message.from_user.id} changed language to {patient.language}')
    update.message.reply_text(messages[patient.language]['language_updated'])
    return config_menu(update, context)


def view_profile(update, context):
    patient = context.user_data['patient']
    message = messages[patient.language]['show_profile'].format(patient.name, patient.gender,
                                                                patient.language,
                                                                patient.schedule.strftime('%H:%M'))
    update.message.reply_text(message, parse_mode=ParseMode.HTML)
    return config_menu(update, context)


def ask_delete_user(update, context):
    patient = context.user_data['patient']
    logger.info(
        f'User {update.message.from_user.username} id {update.message.from_user.id} wants to delete his account.')
    update.message.reply_text(messages[patient.language]['delete_user'],
                              reply_markup=keyboards.delete_user_keyboard[patient.language])
    return PROCESS_DELETE_USER


def ask_change_schedule(update, context):
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} asked to change schedule')
    schedule_dt = UTCTime.to_locale(patient.schedule)
    schedule = schedule_dt.strftime("%H:%M")
    update.message.reply_text(
        messages[patient.language]['current_schedule'] + schedule)
    update.message.reply_text(messages[patient.language]['change_schedule'],
                              reply_markup=ReplyKeyboardRemove())
    return PROCESS_SCHEDULE


@run_async
def process_change_schedule(update, context):
    patient = context.user_data['patient']
    old_schedule = patient.schedule
    new_schedule = update.message.text
    new_schedule_dt = UTCTime.get_utc_result(new_schedule)
    patient.schedule = new_schedule
    patient.save(())
    for old_job in context.job_queue.get_jobs_by_name(f'{update.message.from_user.id}_pending_questions_job'):
        old_job.schedule_removal()
    PendingQuestionJob(context, patient.identifier)
    logger.info(
        f'User {update.message.from_user.username} id {update.message.from_user.id} changed schedule to {patient.schedule}')
    update.message.reply_text(messages[patient.language]['schedule_updated'])
    now = datetime.utcnow()
    # If the time is less than the actual time, question job will start (it will show config menu when patient finishes
    # answering). Otherwise, show config menu
    if new_schedule_dt.time() > now.time():
        return config_menu(update, context)
    else:
        return CHOOSING


@run_async
def process_delete_user(update, context):
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} deleted his account.')
    patient.delete()
    update.message.reply_text(messages[patient.language]['deleted_user'],
                              reply_markup=keyboards.start_keyboard)
    return ConversationHandler.END


def cancel(update, context):
    logger.info(
        f'User {update.message.from_user.username} id {update.message.from_user.id} cancelled current operation.')
    return config_menu(update, context)


def _exit(update, context):
    patient = context.user_data['patient']
    logger.info(f'User {update.message.from_user.username} id {update.message.from_user.id} close the configurator.')
    update.message.reply_text(messages[patient.language]['exit_configurator'],
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


config_handler = ConversationHandler(
    entry_points=[CommandHandler('config', config)],
    states={
        CHOOSING: [MessageHandler(Filters.regex('^(Cambiar imagen de perfil|Change profile picture)$'),
                                  ask_profile_pic),
                   MessageHandler(Filters.regex('^(Cambiar nombre|Change name)$'), ask_change_name),
                   MessageHandler(Filters.regex('^(Cambiar género|Change gender)$'), ask_change_gender),
                   MessageHandler(Filters.regex(f'^(Cambiar idioma|Change language)$'),
                                  ask_change_language),
                   MessageHandler(Filters.regex(f'^(Ver mi perfil|View my profile)$'),
                                  view_profile),
                   MessageHandler(Filters.regex(f'^(Borrar usuario️|Remove user️)$'),
                                  ask_delete_user),
                   MessageHandler(Filters.regex('^(Cambiar horario|Change schedule)$'), ask_change_schedule)
                   ],
        PROCESS_GENDER: [
            MessageHandler(Filters.regex('^(Male|Female|Other|Masculino|Femenino|Otro)$'), process_gender)],
        PROCESS_PROFILE_PIC: [MessageHandler(Filters.photo, process_profile_pic)],
        PROCESS_NAME: [MessageHandler(~is_answering_filter & ~Filters.command, process_name)],
        PROCESS_LANGUAGE: [MessageHandler(Filters.regex(f'^({Flag.flag("es")}|{Flag.flag("gb")})$'),
                                          process_language)],
        PROCESS_DELETE_USER: [MessageHandler(Filters.regex(f'^(Sí, eliminar mi usuario|Yes, delete my user)$'),
                                             process_delete_user)],
        PROCESS_SCHEDULE: [MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'),
                                          process_change_schedule)]
    },
    fallbacks=[CommandHandler('cancel', cancel),
               CommandHandler('exit', _exit)],
    name="configurator"
)
