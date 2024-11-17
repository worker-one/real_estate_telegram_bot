import logging
import logging.config
import os
from time import sleep

from omegaconf import OmegaConf
import telebot
from dotenv import find_dotenv, load_dotenv

from real_estate_telegram_bot.api.handlers.query import send_files
from real_estate_telegram_bot.service.google import GoogleDriveAPI
from real_estate_telegram_bot.db import crud


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
