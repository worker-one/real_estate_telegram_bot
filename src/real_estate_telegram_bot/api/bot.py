import logging
import logging.config
import os

import telebot
from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf

from real_estate_telegram_bot.api.handlers import admin, menu, query, welcome

logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/real_estate_telegram_bot/conf/logging_config.yaml"), resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(usecwd=True))  # Load environment variables from .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logger.error(msg="BOT_TOKEN is not set in the environment variables.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

query.register_handlers(bot)
welcome.register_handlers(bot)
menu.register_handlers(bot)
admin.register_handlers(bot)

def start_bot():
    logger.info(msg=f"Bot `{str(bot.get_me().username)}` has started")
    #bot.infinity_polling()
    bot.polling()
