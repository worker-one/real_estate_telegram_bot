import logging.config
import os

import openpyxl
import pandas as pd
from omegaconf import OmegaConf
from openpyxl.styles import Alignment
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.utils.file import format_excel_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/strings.yaml")

# Custom sorting key
def custom_sort_key(val):
    if isinstance(val, str):
        return (0, val)  # Strings get a tuple with 0 as the first element
    else:
        return (1, val)  # Integers get a tuple with 1 as the first element

def create_main_menu_button(strings):
    main_menu_button = InlineKeyboardMarkup(row_width=1)
    main_menu_button.add(InlineKeyboardButton(strings.main_menu, callback_data="_main_menu"))
    return main_menu_button

def create_create_query_menu(strings):
    query_menu = InlineKeyboardMarkup(row_width=2)
    query_menu.add(InlineKeyboardButton(strings.menu.query, callback_data="_query"))
    query_menu.add(InlineKeyboardButton(strings.main_menu, callback_data="_main_menu"))
    return query_menu

def create_areas_menu_markup(strings: dict, lang: str):
    areas_menu_markup = InlineKeyboardMarkup(row_width=2)
    areas_menu_markup.add(
        InlineKeyboardButton(strings.areas.al_furjan, callback_data="_al_furjan"),
        InlineKeyboardButton(strings.areas.arjan, callback_data="_arjan"),
        InlineKeyboardButton(strings.areas.beachfront, callback_data="_beachfront"),
        InlineKeyboardButton(strings.areas.bluewaters, callback_data="_bluewaters"),
        InlineKeyboardButton(strings.areas.business_bay, callback_data="_business_bay"),
        InlineKeyboardButton(strings.areas.city_walk, callback_data="_city_walk"),
        InlineKeyboardButton(strings.areas.creek_harbour, callback_data="_creek_harbour"),
        InlineKeyboardButton(strings.areas.downtown, callback_data="_downtown"),
        InlineKeyboardButton(strings.areas.dubai_hills, callback_data="_dubai_hills"),
        InlineKeyboardButton(strings.areas.dubai_islands, callback_data="_dubai_islands"),
        InlineKeyboardButton(strings.areas.dubai_marina, callback_data="_dubai_marina"),
        InlineKeyboardButton(strings.areas.dubai_maritime_city, callback_data="_dubai_maritime_city"),
        InlineKeyboardButton(strings.areas.jlt, callback_data="_jlt"),
        InlineKeyboardButton(strings.areas.jvc, callback_data="_jvc"),
        InlineKeyboardButton(strings.areas.jvt, callback_data="_jvt"),
        InlineKeyboardButton(strings.areas.jbr, callback_data="_jbr"),
        InlineKeyboardButton(strings.areas.la_mer, callback_data="_la_mer"),
        InlineKeyboardButton(strings.areas.mina_rashid, callback_data="_mina_rashid"),
        InlineKeyboardButton(strings.areas.palm_jumeirah, callback_data="_palm_jumeirah"),
        InlineKeyboardButton(strings.areas.sobha_hartland, callback_data="_sobha_hartland"),
        InlineKeyboardButton(strings[lang].query.enter_own_area, callback_data="_enter_own_area")
    )
    return areas_menu_markup

def register_handlers(bot):
    # Query area names table
    @bot.callback_query_handler(func=lambda call: call.data == "_area_names")
    def get_area_names_table(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        # Send the downloaded file to the user
        with open("./data/dubai_area_names.xlsx", 'rb') as file:
            bot.send_document(user_id, file, reply_markup=create_main_menu_button(strings[lang])
        )

    # Areas menu handler
    @bot.callback_query_handler(func=lambda call: call.data == "_areas")
    def areas_menu_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        logger.info({"user_id": user_id, "message": call.data})

        bot.send_message(
            call.message.chat.id, strings[lang].menu.select_area,
            reply_markup=create_areas_menu_markup(strings, lang)
        )

    # Specific area handlers (e.g., for "Dubai Marina")
    @bot.callback_query_handler(func=lambda call: call.data in [
    "_dubai_marina", "_business_bay", "_downtown", "_creek_harbour", "_sobha_hartland", "_city_walk",
    "_al_furjan", "_arjan", "_beachfront", "_bluewaters", "_dubai_hills", "_dubai_islands",
    "_dubai_maritime_city", "_jlt", "_jvc", "_jvt", "_jbr", "_la_mer", "_mina_rashid",
    "_palm_jumeirah"])
    def area_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        if call.data == "_jlt":
            area_name = "Jumeirah Lakes Towers"
        elif call.data == "_jvc":
            area_name = "Jumeirah Village Circle"
        elif call.data == "_jvt":
            area_name = "Jumeirah Village Triangle"
        elif call.data == "_jbr":
            area_name = "Jumeirah Beach Residence"

        area_name = call.data[1:].replace("_", " ").title()  # Format the area name from the callback data
        building_data = crud.get_buildings_by_area(area_name)

        # Create a pandas DataFrame from the sorted data
        df = pd.DataFrame(building_data)

        # reverse sorting
        df = df.sort_values(by=['Construction end date'], ascending=False)
        
        # Convert 'Construction end date' to format "dd-mm-yyyy"
        df['Construction end date'] = df['Construction end date'].dt.strftime('%d-%m-%Y')

        # We divide the table into those under construction (OFF PLAN) and finished housing in the area (READY):
        ready_mask = df['Completion %'] == 100
        off_plane_mask = df['Completion %'] != 100
        for mask, name in zip([ready_mask, off_plane_mask], ['ready', 'off_plan']):
            # Define the filename for the Excel file
            filename = f"{area_name}_buildings_{name}.xlsx"
            filepath = os.path.join("./tmp", filename)  # Save it to a temporary directory

            # Save the DataFrame to a local Excel file
            df[mask].to_excel(filepath, index=False)

            # Format the Excel file
            format_excel_file(filepath)

            # Send the formatted Excel file to the user
            with open(filepath, 'rb') as file:
                bot.send_document(user_id, file, reply_markup=create_main_menu_button(strings[lang]))

            # Delete the Excel file after sending it
            os.remove(filepath)

    # Handle the option where the user enters their own area name
    @bot.callback_query_handler(func=lambda call: call.data == "_enter_own_area")
    def enter_own_area_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language
        msg = bot.send_message(call.message.chat.id, strings[lang].query.enter_own_area)
        bot.register_next_step_handler(msg, process_area_name)

    def process_area_name(message):
        user_id = message.from_user.id
        area_name = message.text
        user = crud.read_user(user_id)
        lang = user.language
        building_data = crud.get_buildings_by_area(area_name)
        if building_data:
            # Create a pandas DataFrame from the sorted data
            df = pd.DataFrame(building_data)

            # reverse sorting
            df = df.sort_values(by=['Construction end date'], ascending=False)

            # Convert 'Construction end date' to format "dd-mm-yyyy"
            df['Construction end date'] = df['Construction end date'].dt.strftime('%d-%m-%Y')

            # We divide the table into those under construction (OFF PLAN) and finished housing in the area (READY):
            ready_mask = df['Completion %'] == 100
            off_plane_mask = df['Completion %'] != 100
            for mask, name in zip([ready_mask, off_plane_mask], ['ready', 'off_plan']):
                # Define the filename for the Excel file
                filename = f"{area_name}_buildings_{name}.xlsx"
                filepath = os.path.join("./tmp", filename)  # Save it to a temporary directory

                # Save the DataFrame to a local Excel file
                df[mask].to_excel(filepath, index=False)

                # Format the Excel file
                format_excel_file(filepath)

                # Send the formatted Excel file to the user
                with open(filepath, 'rb') as file:
                    bot.send_document(user_id, file, reply_markup=create_main_menu_button(strings[lang]))

                # Delete the Excel file after sending it
                os.remove(filepath)
        else:
            bot.send_message(
                message.chat.id,
                strings[lang].area_query.result_negative,
                reply_markup=create_create_query_menu(strings[lang])
            )
