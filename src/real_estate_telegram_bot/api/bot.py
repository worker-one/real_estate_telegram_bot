import logging
import logging.config
import os

import telebot
from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf

from real_estate_telegram_bot.api.handlers import admin, areas, common, menu, query, service_charge, welcome
from real_estate_telegram_bot.api.middlewares.antiflood import AntifloodMiddleware
from real_estate_telegram_bot.api.middlewares.user import UserCallbackMiddleware, UserMessageMiddleware

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
    logger.info(f"{config.app.name} v{config.app.version}")

    bot = telebot.TeleBot(BOT_TOKEN, use_class_middlewares=True)

    # Handlers
    common.register_handlers(bot)
    query.register_handlers(bot)
    welcome.register_handlers(bot)
    menu.register_handlers(bot)
    admin.register_handlers(bot)
    areas.register_handlers(bot)
    service_charge.register_handlers(bot)

    # Middlewares
    if config.antiflood.enabled:
        logger.info(f"Antiflood middleware enabled with time window: {config.antiflood.time_window_seconds} seconds")
        bot.setup_middleware(AntifloodMiddleware(bot, config.antiflood.time_window_seconds))
    bot.setup_middleware(UserMessageMiddleware())
    bot.setup_middleware(UserCallbackMiddleware())

    logger.info(msg=f"Bot `{str(bot.get_me().username)}` has started")
    bot.infinity_polling(timeout=290)
    #bot.polling()
