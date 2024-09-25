import datetime
import logging
from telebot import types
from threading import Timer
from omegaconf import OmegaConf
from real_estate_telegram_bot.db.crud import read_user


config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = config.strings

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/real_estate_telegram_bot/conf/logging_config.yaml"),
    resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)


# react to any text if not command
def register_handlers(bot):
    @bot.message_handler(commands=["public_message"])
    def query_handler(message):
        user_id = message.from_user.id
        user = read_user(user_id)
        lang = user.language

        if user.username not in ["hunkydory_uae", "konverner"]:
            # inform that the user does not have rights
            bot.send_message(user_id, strings[lang].no_rights)
            return

        # Ask user to prerecord a message
        sent_message = bot.send_message(user_id, strings[lang].record_message_prompt)
        
        # Register next step for saving the message content
        bot.register_next_step_handler(sent_message, get_message_content, bot, user_id, lang)


def get_message_content(message, bot, user_id, lang):
    prerecorded_message = message.text

    # Ask for datetime input
    sent_message = bot.send_message(user_id, strings[lang].enter_datetime_prompt)
    
    # Register next step for saving the datetime
    bot.register_next_step_handler(sent_message, schedule_message, bot, user_id, lang, prerecorded_message)


def schedule_message(message, bot, user_id, lang, prerecorded_message):
    try:
        # Parse the input datetime
        send_datetime = datetime.datetime.strptime(message.text, "%Y-%m-%d %H:%M:%S")
        current_datetime = datetime.datetime.now()

        # Calculate the delay (in seconds) to send the message
        delay = (send_datetime - current_datetime).total_seconds()

        if delay < 0:
            bot.send_message(user_id, strings[lang].past_datetime_error)
            return

        # Confirm the message is scheduled
        bot.send_message(user_id, strings[lang].message_scheduled_confirmation.format(send_datetime))

        # Schedule the message sending
        Timer(delay, send_scheduled_message, [bot, prerecorded_message, user_id]).start()

    except ValueError:
        bot.send_message(user_id, strings[lang].invalid_datetime_format)


def send_scheduled_message(bot, prerecorded_message, user_id):
    # Send the prerecorded message at the scheduled time
    bot.send_message(user_id, prerecorded_message)
