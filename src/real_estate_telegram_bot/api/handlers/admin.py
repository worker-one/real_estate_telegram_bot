import datetime
import logging
import logging.config
from datetime import datetime

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from real_estate_telegram_bot.db.crud import read_user, read_users

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/strings.yaml")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Paris timezone
timezone = pytz.timezone(config.timezone)

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
def send_scheduled_message(bot, user_id, media_type, message_text: str = None, message_photo: str = None):
    if media_type == 'text':
        bot.send_message(chat_id=user_id, text=message_text)
    elif media_type == 'photo':
        # Fetch the photo by file ID
        if message_text:
            bot.send_photo(chat_id=user_id, caption=message_text, photo=message_photo)
        else:
            bot.send_photo(chat_id=user_id, photo=message_photo)

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
            user_datetime_localized = timezone.localize(user_datetime_obj)

            # Store the datetime and move to the next step (waiting for the message content)
            user_data[user_id] = {'datetime': user_datetime_localized}
            bot.send_message(user_id, strings[lang].record_message_prompt)

            # Move to the next step: receiving the custom message
            bot.register_next_step_handler(message, get_message_content, bot, user_id, lang)

        except ValueError:
            # Handle invalid date format
            bot.send_message(user_id, strings[lang].invalid_datetime_format)

            # Send the admin menu
            bot.send_message(
                user_id, strings[lang].admin_menu.title,
                reply_markup=create_admin_menu_markup(strings[lang])
            )

    # Handler to capture the custom message from the user
    def get_message_content(message, bot, user_id, lang):
        user_message = None
        photo_file = None
        if message.text:
            user_message = message.text
            media_type = 'text'
        elif message.photo:
            # Get the highest quality image (last item in the list)
            photo_file = message.photo[-1].file_id
            user_message = message.caption
            media_type = 'photo'

        # Retrieve the previously stored datetime
        scheduled_datetime = user_data[user_id]['datetime']

        # Schedule the message for the specified datetime
        users = read_users()
        for user in users:
            scheduler.add_job(
                send_scheduled_message, 'date',
                run_date=scheduled_datetime, 
                args=[bot, user.user_id, media_type, user_message, photo_file]
            )

        # Inform the user that the message has been scheduled
        response = strings[lang].message_scheduled_confirmation.format(
            n_users=len(users),
            send_datetime=scheduled_datetime.strftime('%Y-%m-%d %H:%M'),
            timezone=config.timezone
        )
        bot.send_message(user_id, response)

        # Clear the user data to avoid confusion
        del user_data[user_id]

# Start the scheduler
scheduler.start()

