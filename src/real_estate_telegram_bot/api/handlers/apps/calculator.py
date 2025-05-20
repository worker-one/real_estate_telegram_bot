import logging

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/apps/calculator.yaml")
strings = config.strings

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_main_menu_button(lang: str):
    main_menu_button = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    main_menu_button.add(KeyboardButton(strings[lang].main_menu))
    return main_menu_button

def register_handlers(bot):
    """ Register the service charge handlers """
    logger.info("Registering service charge handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "_calculator")
    def show_service_charge(call, data: dict):
        user = data["user"]
        # Send the buttons to the user

        inline_keyboard_markup = InlineKeyboardMarkup()
        inline_keyboard_markup.row(
            InlineKeyboardButton(
                strings[user.lang].start,
                web_app=WebAppInfo(config.app.base_url)
            )
        )

        bot.send_message(user.id, strings[user.lang].start, reply_markup=inline_keyboard_markup)