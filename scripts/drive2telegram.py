import logging
import logging.config
import os
from time import sleep

import telebot
from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf
import re
from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.service.google import GoogleDriveAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(usecwd=True))  # Load environment variables from .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logger.error(msg="BOT_TOKEN is not set in the environment variables.")
    exit(1)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

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


@bot.message_handler(commands=["start"])
def start(message):
    for file_id, _ in google_drive_api.dir_index.items():
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

bot.polling(timeout=723, non_stop=True)
