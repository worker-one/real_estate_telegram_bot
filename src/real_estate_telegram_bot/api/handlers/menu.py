import logging.config

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message, ReplyKeyboardMarkup

from real_estate_telegram_bot.api.users import check_user_in_channel_sync
from real_estate_telegram_bot.db import crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/strings.yaml")
query_strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/apps/query.yaml").strings

# Custom sorting key
def custom_sort_key(val):
    if isinstance(val, str):
        return (0, val)  # Strings get a tuple with 0 as the first element
    else:
        return (1, val)  # Integers get a tuple with 1 as the first element

def create_main_menu_markup(lang: str) -> InlineKeyboardMarkup:
    menu_markup = InlineKeyboardMarkup(row_width=1)
    menu_markup.add(
        InlineKeyboardButton(strings[lang].menu.query, callback_data="_query"),
        InlineKeyboardButton(strings[lang].menu.areas, callback_data="_areas"),
        InlineKeyboardButton(strings[lang].menu.query_files, callback_data="_query_files"),
        InlineKeyboardButton(strings[lang].menu.service_charge, callback_data="_service_charge"),
        InlineKeyboardButton(strings[lang].menu.language, callback_data="_language"),
        InlineKeyboardButton(strings[lang].menu.support, callback_data="_support"),
        InlineKeyboardButton(strings[lang].menu.useful_links, callback_data="_useful_links"),
    )
    return menu_markup

def create_lang_menu_markup(lang: str) -> InlineKeyboardMarkup:
    lang_menu_markup = InlineKeyboardMarkup(row_width=1)
    lang_menu_markup.add(
        InlineKeyboardButton(strings[lang].language_en, callback_data="_en"),
        InlineKeyboardButton(strings[lang].language_ru, callback_data="_ru")
    )
    return lang_menu_markup

def create_main_menu_button(lang: str) -> InlineKeyboardMarkup:
    main_menu_button = ReplyKeyboardMarkup(resize_keyboard=True)
    main_menu_button.add(KeyboardButton(strings[lang].main_menu))
    return main_menu_button

def create_create_query_menu(lang: str) -> InlineKeyboardMarkup:
    query_menu = InlineKeyboardMarkup(row_width=2)
    query_menu.add(InlineKeyboardButton(strings[lang].menu.query, callback_data="_query"))
    query_menu.add(InlineKeyboardButton(strings[lang].main_menu, callback_data="_main_menu"))
    return query_menu

def register_handlers(bot):
    @bot.message_handler(commands=["start", "menu"])
    def menu_menu_command(message, data: dict):
        user = data["user"]
        # Check if user is in the channel
        if check_user_in_channel_sync(config.channel_name, user.username) is False:
            bot.send_message(
                message.chat.id,
                f"You need to join the channel @{config.channel_name} to use the bot."
            )
            return

        lang = user.lang
        logger.info({"user_id": message.from_user.id, "message": message.text})

        bot.send_message(
            message.chat.id, strings[lang].start,
            reply_markup=create_main_menu_markup(lang)
        )

    @bot.message_handler(
        func=lambda message: message.text in {strings["en"].main_menu, strings["ru"].main_menu}
    )
    def menu_menu_command(message: Message, data: dict):
        user = data["user"]
        # Check if user is in the channel
        if check_user_in_channel_sync(config.channel_name, user.username) is False:
            bot.send_message(
                message.chat.id,
                f"You need to join the channel @{config.channel_name} to use the bot."
            )
            return

        lang = user.lang
        logger.info({"user_id": message.from_user.id, "message": message.text})

        bot.send_message(
            message.chat.id, strings[lang].start,
            reply_markup=create_main_menu_markup(lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "_main_menu")
    def main_menu_callback(call, data: dict):
        user = data["user"]
        lang = user.lang
        bot.send_message(
            call.message.chat.id, strings[lang].start,
            reply_markup=create_main_menu_markup(lang)
        )

    # Language selection
    @bot.callback_query_handler(func=lambda call: call.data == "_language")
    def language(call, data: dict):
        user = data["user"]
        lang = user.lang

        lang_menu_markup = create_lang_menu_markup(lang)
        bot.send_message(call.message.chat.id, "Language", reply_markup=lang_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data == "_ru")
    def language_ru(call):
        user_id = call.from_user.id
        lang = "ru"
        crud.update_user_language(user_id, new_language=lang)

        bot.send_message(
            call.message.chat.id, strings[lang].language_selected,
            reply_markup=create_main_menu_button(lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "_en")
    def language_en(call):
        user_id = call.from_user.id
        lang = "en"
        crud.update_user_language(user_id, new_language=lang)
        bot.send_message(
            call.message.chat.id, strings[lang].language_selected,
            reply_markup=create_main_menu_button(lang)
        )


    # Useful links
    @bot.callback_query_handler(func=lambda call: call.data == "_useful_links")
    def useful_links(call, data: dict):
        user = data["user"]
        lang = user.lang

        bot.send_message(call.message.chat.id, strings[lang].useful_links,
            reply_markup=create_main_menu_button(lang)
        )

    # Help
    @bot.callback_query_handler(func=lambda call: call.data == "_support")
    def support(call, data: dict):
        user = data["user"]
        lang = user.lang

        bot.send_message(call.message.chat.id, strings[lang].support,
            reply_markup=create_main_menu_button(lang)
        )

    # Query
    @bot.callback_query_handler(func=lambda call: call.data == "_query")
    def query(call, data: dict):
        user = data["user"]
        lang = user.lang
        bot.send_message(
            call.message.chat.id, query_strings[lang].ask_name,
            reply_markup=create_main_menu_button(lang)
        )
