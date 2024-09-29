import logging.config
from ast import In
from turtle import up

from omegaconf import OmegaConf
from real_estate_telegram_bot.api.users import check_user_in_channel_sync
from real_estate_telegram_bot.db.crud import read_user, upsert_user
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/real_estate_telegram_bot/conf/logging_config.yaml"),
    resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = config.strings

def create_main_menu_markup(strings):
    menu_markup = InlineKeyboardMarkup(row_width=1)
    menu_markup.add(
        InlineKeyboardButton(strings.menu.query, callback_data="_query"),
        InlineKeyboardButton(strings.menu.useful_links, callback_data="_useful_links"),
        InlineKeyboardButton(strings.menu.support, callback_data="_support"),
        InlineKeyboardButton(strings.menu.language, callback_data="_language"),
    )
    return menu_markup

def create_lang_menu_markup(strings):
    lang_menu_markup = InlineKeyboardMarkup(row_width=1)
    lang_menu_markup.add(
        InlineKeyboardButton(strings.language_en, callback_data="_en"),
        InlineKeyboardButton(strings.language_ru, callback_data="_ru")
    )
    return lang_menu_markup

def create_main_menu_button(strings):
    main_menu_button = InlineKeyboardMarkup(row_width=1)
    main_menu_button.add(InlineKeyboardButton(strings.main_menu, callback_data="_main_menu"))
    return main_menu_button


def register_handlers(bot):
    @bot.message_handler(commands=["menu"])
    def menu_menu_command(message):

        user_id = message.from_user.id
        username = message.from_user.username

        # Check if user is in the channel
        if check_user_in_channel_sync(config.channel_name, username) is False:
            bot.send_message(
                message.chat.id,
                f"You need to join the channel @{config.channel_name} to use the bot."
            )
            return
        upsert_user(user_id, username)

        user = read_user(user_id)
        lang = user.language
        logger.info({"user_id": message.from_user.id, "message": message.text})

        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(message.chat.id, strings[lang].main_menu, reply_markup=main_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data == "_main_menu")
    def main_menu_callback(call):
        user_id = call.message.from_user.id
        username = call.message.from_user.username
        upsert_user(user_id, username)

        user = read_user(user_id)
        lang = user.language
        logger.info({"user_id": call.message.from_user.id, "message": call.data})

        main_menu_markup = create_main_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, strings[lang].main_menu, reply_markup=main_menu_markup)

    # Language selection
    @bot.callback_query_handler(func=lambda call: call.data == "_language")
    def language(call):
        user_id = call.from_user.id
        user = read_user(user_id)
        lang = user.language

        logger.info({"user_id": call.from_user.id, "message": call.data})

        lang_menu_markup = create_lang_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, "Language", reply_markup=lang_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data == "_ru")
    def language_ru(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        username = call.from_user.username

        upsert_user(user_id, username, language="ru")
        user = read_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].language_selected)

    @bot.callback_query_handler(func=lambda call: call.data == "_en")
    def language_en(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        username = call.from_user.username

        upsert_user(user_id, username, language="en")
        user = read_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].language_selected)

    # Useful links
    @bot.callback_query_handler(func=lambda call: call.data == "_useful_links")
    def useful_links(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = read_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].useful_links)

    # Help
    @bot.callback_query_handler(func=lambda call: call.data == "_support")
    def support(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = read_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].support)

    # Query
    @bot.callback_query_handler(func=lambda call: call.data == "_query")
    def query(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = read_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].query.ask_name)
