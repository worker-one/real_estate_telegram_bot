import logging
import logging.config
import os
import threading

import telebot
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from omegaconf import OmegaConf
from telebot.states.sync.middleware import StateMiddleware

from real_estate_telegram_bot.api.handlers import admin, apps
from real_estate_telegram_bot.api.middlewares.antiflood import AntifloodMiddleware
from real_estate_telegram_bot.api.middlewares.user import UserCallbackMiddleware, UserMessageMiddleware
from real_estate_telegram_bot.api.routes import calculator as calculator_routes
from real_estate_telegram_bot.api.routes import health as health_routes

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logger.error(msg="BOT_TOKEN is not set in the environment variables.")
    exit(1)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

def start_bot():
    logger.info(f"{config.name} v{config.version}")

    bot = telebot.TeleBot(BOT_TOKEN, use_class_middlewares=True)

    # Handlers
    apps.register_handlers(bot)
    admin.register_handlers(bot)

    # Routes
    app = FastAPI()
    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(calculator_routes.create_router(bot))
    app.include_router(health_routes.create_router(bot))

    # Run app in parallel
    threading.Thread(target=uvicorn.run, kwargs={"app": app, "host": config.host, "port": config.port}).start()

    # Middlewares
    if config.antiflood.enabled:
        logger.info(f"Antiflood middleware enabled with time window: {config.antiflood.time_window_seconds} seconds")
        bot.setup_middleware(AntifloodMiddleware(bot, config.antiflood.time_window_seconds))
    bot.setup_middleware(UserMessageMiddleware())
    bot.setup_middleware(UserCallbackMiddleware())
    bot.setup_middleware(StateMiddleware(bot))

    logger.info(msg=f"Bot `{str(bot.get_me().username)}` has started")
    bot.infinity_polling(timeout=290)
    #bot.polling()
