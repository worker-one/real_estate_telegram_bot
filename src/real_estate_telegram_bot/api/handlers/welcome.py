import logging

from omegaconf import OmegaConf

from real_estate_telegram_bot.db.crud import upsert_user

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
lang = config.lang
strings = config.stringsstrings = OmegaConf.load("./src/real_estate_telegram_bot/conf/strings.yaml")


# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def start_handler(message):

        user_id = message.from_user.id
        username = message.from_user.username
        upsert_user(user_id, username)

        #lang = user.lang

        bot.reply_to(message, strings["en"].start)

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
