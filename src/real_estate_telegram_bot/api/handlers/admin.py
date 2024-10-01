import datetime
import logging
import logging.config
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from omegaconf import OmegaConf
from real_estate_telegram_bot.db.crud import read_user, read_users
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
import pytz

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = config.strings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Paris timezone
TIMEZONE = 'Asia/Dubai'
paris_timezone = pytz.timezone(TIMEZONE)

# Initialize the scheduler
scheduler = BackgroundScheduler()

# Dictionary to store user data during message scheduling
user_data = {}

def create_admin_menu_markup(strings):
    menu_markup = InlineKeyboardMarkup(row_width=1)
    menu_markup.add(
        InlineKeyboardButton(strings.admin_menu.send_message, callback_data="_public_message"),
    )
    return menu_markup


# Function to send a scheduled message
def send_scheduled_message(bot, chat_id, message_text):
    bot.send_message(chat_id, message_text)


# React to any text if not command
def register_handlers(bot):
    @bot.message_handler(commands=["admin"])
    def admin_menu_command(message):
        user_id = message.from_user.id
        user = read_user(user_id)
        lang = user.language

        if user.username not in config.admins:
            # Inform the user that they do not have admin rights
            bot.send_message(user_id, strings[lang].no_rights)
            return

        # Send the admin menu
        bot.send_message(
            user_id, strings[lang].admin_menu.title,
            reply_markup=create_admin_menu_markup(strings[lang])
        )

    @bot.callback_query_handler(func=lambda call: call.data == "_public_message")
    def query_handler(call):
        user_id = call.from_user.id
        user = read_user(user_id)
        lang = user.language

        if user.username not in config.admins:
            # Inform that the user does not have admin rights
            bot.send_message(user_id, strings[lang].no_rights)
            return

        # Ask user to provide the date and time
        sent_message = bot.send_message(user_id, strings[lang].enter_datetime_prompt)
        # Move to the next step: receiving the datetime input
        bot.register_next_step_handler(sent_message, get_datetime_input, bot, user_id, lang)

    # Handler to capture the datetime input from the user
    def get_datetime_input(message, bot, user_id, lang):
        user_input = message.text
        try:
            # Parse the user's input into a datetime object
            user_datetime_obj = datetime.strptime(user_input, '%Y-%m-%d %H:%M')

            # Localize the time to Paris timezone
            user_datetime_localized = paris_timezone.localize(user_datetime_obj)

            # Store the datetime and move to the next step (waiting for the message content)
            user_data[user_id] = {'datetime': user_datetime_localized}
            bot.send_message(user_id, strings[lang].record_message_prompt)

            # Move to the next step: receiving the custom message
            bot.register_next_step_handler(message, get_message_content, bot, user_id, lang)

        except ValueError:
            # Handle invalid date format
            bot.send_message(user_id, strings[lang].invalid_datetime_format)
            # Prompt the user again
            bot.register_next_step_handler(message, get_datetime_input, bot, user_id, lang)

    # Handler to capture the custom message from the user
    def get_message_content(message, bot, user_id, lang):
        user_message = message.text

        # Retrieve the previously stored datetime
        scheduled_datetime = user_data[user_id]['datetime']

        # Schedule the message for the specified datetime
        # Schedule the message sending
        users = read_users()
        for user in users:
            print(user.user_id)
            scheduler.add_job(
                send_scheduled_message, 'date',
                run_date=scheduled_datetime, 
                args=[bot, user.user_id, user_message]
        )

        # Inform the user that the message has been scheduled
        response = strings[lang].message_scheduled_confirmation.format(
            n_users = len(users),
            send_datetime = scheduled_datetime.strftime('%Y-%m-%d %H:%M')
        )
        bot.send_message(user_id, response)

        # Clear the user data to avoid confusion
        del user_data[user_id]

# Start the scheduler
scheduler.start()

