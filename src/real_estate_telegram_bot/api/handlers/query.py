import logging
from datetime import datetime

from omegaconf import OmegaConf

from real_estate_telegram_bot.api.endpoints.menu import menu_markup
from real_estate_telegram_bot.db.crud import add_meal, get_aggregate_last_24_hours, get_user_info

app_config = OmegaConf.load("./src/real_estate_telegram_bot/conf/app.yaml")

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

buffer = {}


def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "enter_meal")
    def enter_meal(call):
        bot.send_message(call.message.chat.id, app_config.strings.enter_meal)
        buffer[call.message.chat.id] = {}
        msg = bot.send_message(call.message.chat.id, app_config.strings.enter_calories)
        bot.register_next_step_handler(msg, save_calories)

    def save_calories(message):
        calories = int(message.text)
        buffer[message.chat.id]["calories"] = calories
        msg = bot.send_message(message.chat.id, app_config.strings.enter_proteins)
        bot.register_next_step_handler(msg, save_proteins)