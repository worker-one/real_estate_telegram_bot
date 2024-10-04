import logging

from omegaconf import OmegaConf

from real_estate_telegram_bot.db.crud import upsert_user

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
lang = config.lang
strings = config.strings[lang]

# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_handlers(bot):

    @bot.message_handler(commands=['help'])
    def help_handler(message):

        user_id = message.from_user.id
        username = message.from_user.username
        upsert_user(user_id, username)

        logger.info(f"Received help command from user {message.from_user.id}")
        bot.reply_to(message, strings.help)

    @bot.message_handler(commands=['restart'])
    def help_handler(message):

        user_id = message.from_user.id
        username = message.from_user.username
        upsert_user(user_id, username)
        bot.reply_to(message, "Bot has been restarted")
