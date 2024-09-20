import logging

from omegaconf import OmegaConf

from real_estate_telegram_bot.db.crud import upsert_user

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
lang = config.lang
strings = config.strings[lang]

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/real_estate_telegram_bot/conf/logging_config.yaml"),
    resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start_handler(message):

        user_id = message.from_user.id
        username = message.from_user.username
        upsert_user(user_id, username)

        logger.info(f"Received start command from user {message.from_user.id}")
        bot.reply_to(message, strings.start)

    @bot.message_handler(commands=['help'])
    def help_handler(message):

        user_id = message.from_user.id
        username = message.from_user.username
        upsert_user(user_id, username)

        logger.info(f"Received help command from user {message.from_user.id}")
        bot.reply_to(message, strings.help)
