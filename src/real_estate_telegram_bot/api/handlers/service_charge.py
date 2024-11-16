import datetime
import logging
import os
import re

import pandas as pd
from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from real_estate_telegram_bot.api.handlers.menu import create_main_menu_button
from real_estate_telegram_bot.api.users import check_user_in_channel_sync
from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.utils.file import format_excel_file

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/strings.yaml")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: "_service_charge" in call.data)
    def show_service_charge(call):
        master_project_en = call.data.replace("_service_charge_", "").strip()
        logger.info(f"master_project_en = {master_project_en}")

        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        df = crud.get_project_service_charge_by_year(master_project_en)

        if len(df) != 0:

            # Define the filename for the Excel file
            filename = f"{master_project_en}_service_charge.xlsx"
            filepath = os.path.join("./tmp", filename)  # Save it to a temporary directory

            # Save the DataFrame to a local Excel file
            df.to_excel(filepath, index=False)

            # Format the Excel file
            format_excel_file(filepath, header_color="ed7d31")

            # Send the formatted Excel file to the user
            with open(filepath, 'rb') as file:
                bot.send_document(user_id, file, caption=strings[lang].service_charge.result_positive)

            # Delete the Excel file after sending it
            os.remove(filepath)
        else:
            bot.send_message(user_id, strings[lang].service_charge.result_negative)
