import datetime
import logging
import logging.config
from apscheduler.schedulers.blocking import BlockingScheduler

from omegaconf import OmegaConf
from real_estate_telegram_bot.db.crud import read_user, read_users
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = config.strings

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/real_estate_telegram_bot/conf/logging_config.yaml"),
    resolve=True
)
#logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)


def create_admin_menu_markup(strings):
    menu_markup = InlineKeyboardMarkup(row_width=1)
    menu_markup.add(
        InlineKeyboardButton(strings.admin_menu.send_message, callback_data="_public_message"),
    )
    return menu_markup


# react to any text if not command
def register_handlers(bot):
    @bot.message_handler(commands=["admin"])
    def admin_menu_command(message):
        user_id = message.from_user.id
        user = read_user(user_id)
        lang = user.language

        if user.username not in config.admins:
            # inform that the user does not have rights
            bot.send_message(user_id, strings[lang].no_rights)
            return

        # Send the admin menu
        bot.send_message(
            user_id, strings[lang].admin_menu.title,
            reply_markup=create_admin_menu_markup(strings[lang])
        )

    @bot.callback_query_handler(func=lambda call: call.data == "_public_message")
    def query_handler(message):
        user_id = message.from_user.id
        user = read_user(user_id)
        lang = user.language

        if user.username.lower() not in config.admins:
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


def send_scheduled_message(bot, prerecorded_message, user_id):
    # Send the prerecorded message at the scheduled time
    bot.send_message(user_id, prerecorded_message)


def schedule_message(message, bot, user_id, lang, prerecorded_message):
    # timezone paris with standard logger
    sched = BlockingScheduler(timezone="Europe/Paris", logger=logging.getLogger(__name__))
    try:
        # Parse the input datetime
        send_datetime = datetime.datetime.strptime(message.text, "%Y-%m-%d %H:%M:%S")
        send_datetime = send_datetime.replace(tzinfo=datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=2)))  # Convert to Paris time
        current_datetime = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))  # Current time in Paris time

        # Calculate the delay (in seconds) to send the message
        delay = (send_datetime - current_datetime).total_seconds()

        if delay < 0:
            bot.send_message(user_id, strings[lang].past_datetime_error)
            return

        # Confirm the message is scheduled
        bot.send_message(
            user_id,
            strings[lang].message_scheduled_confirmation.format(send_datetime=send_datetime)
        )

        # Schedule the message sending
        users = read_users()
        for user in users:
            logger.info(msg=f"Scheduling message for user {user.user_id} at {send_datetime}")
            sched.add_job(
                send_scheduled_message,
                "date",
                run_date=send_datetime,
                args=[bot, prerecorded_message, user.user_id]
            )
            # every 5 minutes
            sched.add_job(
                send_scheduled_message,
                "interval",
                minutes=5,
                start_date=send_datetime,
                end_date=send_datetime,
                args=[bot, prerecorded_message, user.user_id]
            )
            # with cron trigger
            sched.add_job(
                send_scheduled_message,
                "cron",
                day_of_week='mon-sun',
                hour=send_datetime.hour,
                minute=send_datetime.minute,
                second=send_datetime.second,
                args=[bot, prerecorded_message, user.user_id]
            )

        sched.start()
        # list all jobs
        sched.print_jobs()

    except ValueError:
        bot.send_message(user_id, strings[lang].invalid_datetime_format)

