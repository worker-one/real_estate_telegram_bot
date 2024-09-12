import os
import telebot
import logging
import logging.config
from dotenv import load_dotenv, find_dotenv
from omegaconf import OmegaConf

from telegram_bot.api.handlers import welcome

logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/telegram_bot/conf/logging_config.yaml"), resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(usecwd=True))  # Load environment variables from .env file
TOKEN = os.getenv("BOT_TOKEN")

if TOKEN is None:
    logger.error("BOT_TOKEN is not set in the environment variables.")
    exit(1)

cfg = OmegaConf.load("./src/telegram_bot/conf/config.yaml")
bot = telebot.TeleBot(TOKEN, parse_mode=None)

welcome.register_handlers(bot)

def start_bot():
    logger.info(f"Bot `{str(bot.get_me().username)}` has started")
    bot.infinity_polling()
