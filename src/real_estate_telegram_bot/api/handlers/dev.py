import logging
import logging.config
import os
import re
from time import sleep

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.service.google import GoogleDriveAPI

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/dev/menu.yaml")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


google_drive_api = GoogleDriveAPI()
google_drive_api.load_index()

def send_files(items: list[dict], project_id: int, user_id, bot) -> None:
    for item in items:
        file_name = item['file_name']
        file_id = item['id']

        # Check that file_name has a file extension
        if not re.search(r"\.\w+$", file_name):
            file_name += ".pdf"

        # Check if the file is already in the database
        project_file = crud.get_project_file_by_name(item["file_name"])
        if not project_file:
            logger.info(f"Downloading file {file_name} from Google Drive")

            # Download the file from Google Drive
            google_drive_api.download_file(file_id, file_name)

            # Send the downloaded file to the user
            with open(file_name, 'rb') as file:
                sent_message = bot.send_document(user_id, file)
                # Add the file to the database
                crud.add_project_file(
                    project_id=project_id,
                    file_name=file_name,
                    file_type="pdf",
                    file_telegram_id=sent_message.document.file_id
                )

            # Remove file
            os.remove(file_name)
        else:
            logger.info(f"File {file_name} already exists in the database")
            try:
                bot.send_document(user_id, project_file.file_telegram_id)
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                # download file from google drive
                google_drive_api.download_file(file_id, file_name)

                # Send the downloaded file to the user
                with open(file_name, 'rb') as file:
                    sent_message = bot.send_document(user_id, file)
                    # Add the file to the database
                    crud.update_project_file(
                        project_id=project_id,
                        file_name=file_name,
                        file_type="pdf",
                        file_telegram_id=sent_message.document.file_id
                    )
                    logger.info(f"File {file_name} updated in the database")
                # Remove file
                os.remove(file_name)


def create_dev_menu_markup(lang) -> InlineKeyboardMarkup:
    """Create the dev menu markup."""
    menu_markup = InlineKeyboardMarkup(row_width=1)
    for option in config[lang].dev_menu.options:
        menu_markup.add(InlineKeyboardButton(option.label, callback_data=option.value))
    return menu_markup


def register_handlers(bot):
    """Register the handlers for the dev menu."""

    @bot.message_handler(commands=["drive2telegram"])
    def drive2telegram(message):
        offset = int(message.text.split(" ")[1])
        items = list(google_drive_api.dir_index.items())
        for file_id, _ in items[offset:]:
            try:
                project = crud.query_projects_by_name(file_id)[0]
                print(f"File ID: {file_id}, Project ID: {project.project_id}")
                items = google_drive_api.search(file_id)
                send_files(
                    items, user_id=message.from_user.id, bot=bot,
                    project_id=project.project_id
                )
                sleep(1)
            except:
                logger.error(f"Error processing file {file_id}")
                pass

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
