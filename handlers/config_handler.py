from telegram import ReplyKeyboardRemove, ParseMode
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from config.messages import messages
from howru_helpers import UTCTime
from jobs.PendingQuestionJob import PendingQuestionJob
from log.logger import logger
import keyboards
import manage
from howru_models.models import Patient

PROCESS_PROFILE_PIC, PROCESS_NAME, PROCESS_GENDER, CHOOSING, PROCESS_LANGUAGE, PROCESS_DELETE_USER, PROCESS_SCHEDULE = \
    range(7)


class ConfigHandler(object):
    def __init__(self):
        self.patient = Patient()

    def config_menu(self, update, context):
        context.bot.send_message(chat_id=self.user.id,
                                 text=messages[self.patient.language]['select_config'],
                                 reply_markup=keyboards.config_keyboard[self.patient.language])
        return CHOOSING

    def config(self, update, context):
        self.user = update.message.from_user
        logger.debug(f'User {self.user.username} id {self.user.id} started the configurator')
        try:
            self.patient = Patient.objects.get(identifier=self.user.id)
        except Exception:
            logger.debug(
                f'User {self.user.username} id {self.user.id} tried to start the configurator but was not registered')
            update.message.reply_text('You must register first by clicking /start\n'
                                      'Debes registrarte primero pulsando /start.',
                                      reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        return self.config_menu(update, context)

    def ask_profile_pic(self, update, context):
        # Send current picture
        picture_path = self.patient.picture
        update.message.reply_text(messages[self.patient.language]['current_picture'],
                                  reply_markup=ReplyKeyboardRemove())
        update.message.reply_photo(open(picture_path, 'rb'))
        update.message.reply_text(messages[self.patient.language]['change_picture'], reply_markup=ReplyKeyboardRemove())
        return PROCESS_PROFILE_PIC

    def process_profile_pic(self, update, context):
        photo_file = update.message.photo[-1].get_file()
        pic_name = f'pics/{self.user.id}.jpg'
        photo_file.download(pic_name)
        self.patient.picture = pic_name
        logger.debug(f'User {self.user.username} id {self.user.id} changed profile picture')
        update.message.reply_text(messages[self.patient.language]['picture_updated'],
                                  reply_markup=ReplyKeyboardRemove())
        return self.config_menu(update, context)

    def ask_change_name(self, update, context):
        logger.debug(f'User {self.user.username} id {self.user.id} asked to change name')
        update.message.reply_text(messages[self.patient.language]['current_name'] + self.patient.name)
        update.message.reply_text(messages[self.patient.language]['change_name'], reply_markup=ReplyKeyboardRemove())
        return PROCESS_NAME

    def process_name(self, update, context):
        old_name = self.patient.name
        name = update.message.text
        self.patient.name = name
        logger.debug(f'User {self.user.username} old  name {old_name} id {self.user.id} changed name to {name}')
        update.message.reply_text(messages[self.patient.language]['name_updated'])
        return self.config_menu(update, context)

    def ask_change_gender(self, update, context):
        logger.debug(f'User {self.user.username} id {self.user.id} asked to change gender')
        update.message.reply_text(messages[self.patient.language]['current_gender'] + self.patient.gender)
        update.message.reply_text(messages[self.patient.language]['change_gender'],
                                  reply_markup=keyboards.gender_keyboard[self.patient.language])
        return PROCESS_GENDER

    def process_gender(self, update, context):
        gender = update.message.text
        self.patient.gender = gender
        logger.debug(f'User {self.user.username} id {self.user.id} changed gender to {gender}')
        update.message.reply_text(messages[self.patient.language]['gender_updated'])
        return self.config_menu(update, context)

    def ask_change_language(self, update, context):
        logger.debug(f'User {self.user.username} id {self.user.id} asked to change language')
        update.message.reply_text(messages[self.patient.language]['current_language'] + self.patient.language)
        update.message.reply_text(messages[self.patient.language]['change_language'],
                                  reply_markup=keyboards.language_keyboard)
        return PROCESS_LANGUAGE

    def process_language(self, update, context):
        self.patient.language = update.message.text
        logger.debug(f'User {self.user.username} id {self.user.id} changed language to {self.patient.language}')
        update.message.reply_text(messages[self.patient.language]['language_updated'])
        return self.config_menu(update, context)

    def view_profile(self, update, context):
        message = messages[self.patient.language]['show_profile'].format(self.patient.name, self.patient.gender,
                                                                         self.patient.language,
                                                                         self.patient.schedule.strftime('%H:%M'))
        update.message.reply_text(message, parse_mode=ParseMode.HTML)
        return self.config_menu(update, context)

    def ask_delete_user(self, update, context):
        logger.debug(f'User {self.user.username} id {self.user.id} wants to delete his account.')
        update.message.reply_text(messages[self.patient.language]['delete_user'],
                                  reply_markup=keyboards.delete_user_keyboard[self.patient.language])
        return PROCESS_DELETE_USER

    def ask_change_schedule(self, update, context):
        logger.debug(f'User {self.user.username} id {self.user.id} asked to change schedule')
        schedule_dt = UTCTime.to_locale(self.patient.schedule)
        schedule = schedule_dt.strftime("%H:%M")
        update.message.reply_text(
            messages[self.patient.language]['current_schedule'] + schedule)
        update.message.reply_text(messages[self.patient.language]['change_schedule'],
                                  reply_markup=ReplyKeyboardRemove())
        return PROCESS_SCHEDULE

    def process_change_schedule(self, update, context):
        self.patient.schedule = update.message.text
        for old_job in context.job_queue.get_jobs_by_name(f'{self.user.id}_pending_questions_job'):
            old_job.schedule_removal()
        PendingQuestionJob(context, self.patient.identifier)
        logger.debug(f'User {self.user.username} id {self.user.id} changed schedule to {self.patient.schedule}')
        update.message.reply_text(messages[self.patient.language]['schedule_updated'])
        return ConversationHandler.END

    def process_delete_user(self, update, context):
        logger.info(f'User {self.user.username} id {self.user.id} deleted his account.')
        self.patient.delete_from_db()
        update.message.reply_text(messages[self.patient.language]['deleted_user'],
                                  reply_markup=keyboards.start_keyboard)
        return ConversationHandler.END

    def cancel(self, update, context):
        logger.debug(f'User {self.user.username} id {self.user.id} cancelled current operation.')
        return self.config_menu(update, context)

    def _exit(self, update, context):
        logger.debug(f'User {self.user.username} id {self.user.id} close the configurator.')
        update.message.reply_text(messages[self.patient.language]['exit_configurator'],
                                  reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


instance = ConfigHandler()
config_handler = ConversationHandler(
    entry_points=[CommandHandler('config', instance.config)],
    states={
        CHOOSING: [MessageHandler(Filters.regex('^(Cambiar imagen de perfil|Change profile picture)$'),
                                  instance.ask_profile_pic),
                   MessageHandler(Filters.regex('^(Cambiar nombre|Change name)$'), instance.ask_change_name),
                   MessageHandler(Filters.regex('^(Cambiar género|Change gender)$'), instance.ask_change_gender),
                   MessageHandler(Filters.regex(f'^(Cambiar idioma|Change language)$'),
                                  instance.ask_change_language),
                   MessageHandler(Filters.regex(f'^(Ver mi perfil|View my profile)$'),
                                  instance.view_profile),
                   MessageHandler(Filters.regex(f'^(Borrar usuario️|Remove user️)$'),
                                  instance.ask_delete_user),
                   MessageHandler(Filters.regex('^(Cambiar horario|Change schedule)$'), instance.ask_change_schedule)
                   ],
        PROCESS_GENDER: [
            MessageHandler(Filters.regex('^(Male|Female|Other|Masculino|Femenino|Otro)$'), instance.process_gender)],
        PROCESS_PROFILE_PIC: [MessageHandler(Filters.photo, instance.process_profile_pic)],
        PROCESS_NAME: [MessageHandler(Filters.text, instance.process_name)],
        PROCESS_LANGUAGE: [MessageHandler(Filters.regex(f'^({keyboards.flag("es")}|{keyboards.flag("gb")})$'),
                                          instance.process_language)],
        PROCESS_DELETE_USER: [MessageHandler(Filters.regex(f'^(Sí, eliminar mi usuario|Yes, delete my user)$'),
                                             instance.process_delete_user)],
        PROCESS_SCHEDULE: [MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'),
                                          instance.process_change_schedule)]
    },
    fallbacks=[CommandHandler('cancel', instance.cancel),
               CommandHandler('exit', instance._exit)]
)
