import logging
import logging.config

from omegaconf import OmegaConf
from telebot import types
from real_estate_telegram_bot.api.handlers.common import create_cancel_button
from real_estate_telegram_bot.db import crud

# Load configuration
strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/admin/grant_admin.yaml")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# React to any text if not command
def register_handlers(bot):
    """Register grant admin handlers"""
    logger.info("Registering grant admin handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "add_admin")
    def add_admin_handler(call: types.CallbackQuery, data: dict):
        user = data["user"]

        # Ask for the username
        sent_message = bot.send_message(
            user.id, strings[user.lang].enter_username, reply_markup=create_cancel_button(user.lang)
        )

        # Move to the next step: receiving the custom message
        bot.register_next_step_handler(sent_message, read_username, bot, user)

    def read_username(message, bot, user):
        admin_username = message.text

        # Send prompt to enter user id
        sent_message = bot.send_message(
            user.id, strings[user.lang].enter_user_id, reply_markup=create_cancel_button(user.lang)
        )

        # Move to the next step
        bot.register_next_step_handler(sent_message, read_user_id, bot, user, admin_username)

    def read_user_id(message, bot, user, admin_username):
        admin_user_id = message.text

        new_admin = crud.upsert_user(id=admin_user_id, username=admin_username, role="admin")

        bot.send_message(
            user.id, strings[user.lang].add_admin_confirm.format(user_id=int(new_admin.id), username=new_admin.username)
        )
