from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

from config.messages import messages
from jobs.PendingQuestionJob import PendingQuestionJob
from log.logger import logger
from howru_models import keyboards
from howru_models.Users.Patient import Patient

GENDER, PICTURE, LANGUAGE, SCHEDULE = range(4)


class StartHandler(object):
    def __init__(self):
        pass

    def start(self, update, context):
        self.user = update.message.from_user
        self.patient = Patient(name=self.user.first_name, identifier=self.user.id, username=self.user.username)
        # Check that user is not registered
        if self.patient.exists():
            logger.debug(f'User {self.user.username} id {self.user.id} tried to register again.')
            update.message.reply_text(text=messages[self.patient.language]['already_exists'])
            return ConversationHandler.END

        logger.info(f'User {self.user.username} id {self.user.id} started a new conversation')
        update.message.reply_text(text=f'Hi {self.user.first_name}. Welcome to HOW-R-U psychologist bot.\n'
                                       f'Hola {self.user.first_name}. Bienvenido al bot psicólogo HOW-R-U')
        update.message.reply_text(text=f'Please select a language:\nElija un idioma por favor:',
                                  reply_markup=keyboards.language_keyboard)

        return LANGUAGE

    def language(self, update, context):
        language = update.message.text
        logger.debug(f'User {self.user.username} id {self.user.id} chose language {language}')
        self.patient.language = language
        update.message.reply_text(text=messages[self.patient.language]['choose_gender'],
                                  reply_markup=keyboards.gender_keyboard[self.patient.language])
        return GENDER

    def gender(self, update, context):
        logger.debug(f'User {self.user.username} id {self.user.id} chose gender {update.message.text}')
        update.message.reply_text(messages[self.patient.language]['choose_pic'], reply_markup=ReplyKeyboardRemove())
        self.patient.gender = update.message.text
        return PICTURE

    def picture(self, update, context):
        photo_file = update.message.photo[-1].get_file()
        pic_name = f'pics/{self.user.id}..jpg'
        photo_file.download(pic_name)
        logger.debug(f'User {self.user.username} id {self.user.id} sent picture {pic_name}')
        update.message.reply_text(messages[self.patient.language]['choose_schedule'])
        self.patient.picture = pic_name
        return SCHEDULE

    def skip_picture(self, update, context):
        logger.debug(f'User {self.user.username} id {self.user.id} did not send a picture, using default')
        self.patient.picture = f'pics/default_profile_picture.png'
        update.message.reply_text(messages[self.patient.language]['choose_schedule'])
        return SCHEDULE

    def schedule(self, update, context):
        schedule = update.message.text
        logger.debug(f'User {self.user.username} id {self.user.id} chose schedule {schedule}')
        self.patient.schedule = schedule
        return self.finish(update, context)

    def finish(self, update, context):
        self.patient.to_db()
        update.message.reply_text(messages[self.patient.language]['registration_ok'])
        logger.debug(f'Creating pending_questions job for user {self.user.username}')
        PendingQuestionJob(context, self.patient.identifier)
        return ConversationHandler.END


instance = StartHandler()
start_handler = ConversationHandler(
    entry_points=[CommandHandler('start', instance.start)],
    states={
        LANGUAGE: [MessageHandler(Filters.regex(f'^({keyboards.flag("es")}|{keyboards.flag("gb")})$'),
                                  instance.language)],
        GENDER: [MessageHandler(Filters.regex('^(Male|Female|Other|Masculino|Femenino|Otro)$'), instance.gender)],
        PICTURE: [MessageHandler(Filters.photo, instance.picture), CommandHandler('skip', instance.skip_picture)],
        SCHEDULE: [MessageHandler(Filters.regex('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'), instance.schedule)]
    },
    fallbacks=[]
)
