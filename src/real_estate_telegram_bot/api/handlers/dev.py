import logging
import logging.config

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/dev/menu.yaml")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dev_menu_markup(lang) -> InlineKeyboardMarkup:
    """Create the dev menu markup."""
    menu_markup = InlineKeyboardMarkup(row_width=1)
    for option in config[lang].dev_menu.options:
        menu_markup.add(InlineKeyboardButton(option.label, callback_data=option.value))
    return menu_markup


def register_handlers(bot):
    """Register the handlers for the dev menu."""

    @bot.message_handler(commands=["dev"])
    def dev_menu_command(message: Message, data: dict):
        """Handler to show the dev menu."""
        user = data["user"]
        if user.role != "admin":
            # Inform the user that they do not have dev rights
            bot.send_message(message.from_user.id, config[user.lang].no_rights)
            return

        # Send the dev menu
        bot.send_message(
            message.from_user.id, config[user.lang].dev_menu.title, reply_markup=create_dev_menu_markup(user.lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "get_query_config")
    def get_query_config(call):
        """Handler to get the query config."""
        # Upload config
        config = OmegaConf.load("./src/real_estate_telegram_bot/conf/query.yaml")

        # Send the config
        bot.send_message(call.from_user.id, f"```yaml{config.pretty()}```", parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data == "update_query_config")
    def update_query_config(call):
        """Handler to update the query config."""
        # Inform the user
        bot.send_message(call.from_user.id, "Please send the new query config as a YAML file.")

        bot.register_next_step_handler(call.message, receive_query_config)

    @bot.message_handler(content_types=["document"])
    def receive_query_config(message):
        """Handler to receive the query config."""
        # Download the file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Save the file
        with open("./src/real_estate_telegram_bot/conf/query.yaml", "wb") as new_file:
            new_file.write(downloaded_file)

        # Inform the user
        bot.send_message(message.from_user.id, "Query config updated.")
