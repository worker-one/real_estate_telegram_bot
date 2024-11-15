import logging
import logging.config
import os
from omegaconf import OmegaConf
import telebot
from dotenv import find_dotenv, load_dotenv

from real_estate_telegram_bot.api.handlers import admin, menu, query, welcome, areas, service_charge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(usecwd=True))  # Load environment variables from .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logger.error(msg="BOT_TOKEN is not set in the environment variables.")
    exit(1)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

def start_bot():
    logger.info(f"{config.name} v{config.version}")
    logger.info(msg=f"Bot `{str(bot.get_me().username)}` has started")

    query.register_handlers(bot)
    welcome.register_handlers(bot)
    menu.register_handlers(bot)
    admin.register_handlers(bot)
    areas.register_handlers(bot)
    service_charge.register_handlers(bot)

    bot.infinity_polling(timeout=290)
    #bot.polling()
