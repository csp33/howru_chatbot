from telegram import ReplyKeyboardMarkup

from howru_helpers.Flag import flag


def get_custom_keyboard(values):
    """
    Creates a custom keyboard with response values.
    :param values (str)
    """
    schema = [[str(value)] for value in values]
    return ReplyKeyboardMarkup(schema)


gender_keyboard = {
    'ES': ReplyKeyboardMarkup([['Masculino', 'Femenino', 'Otro']]),
    'GB': ReplyKeyboardMarkup([['Male', 'Female', 'Other']])
}
language_keyboard = ReplyKeyboardMarkup([[flag('es'), flag('gb')]])
delete_user_keyboard = {
    'ES': ReplyKeyboardMarkup([
        ['Sí, eliminar mi usuario']
    ]
    ),
    'GB': ReplyKeyboardMarkup(
        [
            ['Yes, delete my user']
        ]
    ),
}
start_keyboard = ReplyKeyboardMarkup([['/start']])
config_keyboard = {
    'ES': ReplyKeyboardMarkup([
        ['Cambiar imagen de perfil', 'Cambiar nombre'],
        ["Cambiar género", 'Cambiar idioma'],
        ['Cambiar horario', "Ver mi perfil"],
        ["Borrar usuario️"]
    ]
    ),
    'GB': ReplyKeyboardMarkup(
        [
            ['Change profile picture', 'Change name'],
            ["Change gender", 'Change language'],
            ['Change schedule', "View my profile"],
            ["Remove user️"]
        ]
    ),
}
