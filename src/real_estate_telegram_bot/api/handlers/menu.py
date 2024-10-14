import logging.config
import pandas as pd
from io import BytesIO
import os
from omegaconf import OmegaConf
from real_estate_telegram_bot.api.users import check_user_in_channel_sync
from real_estate_telegram_bot.db import crud
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = config.strings

def create_main_menu_markup(strings):
    menu_markup = InlineKeyboardMarkup(row_width=1)
    menu_markup.add(
        InlineKeyboardButton(strings.menu.query, callback_data="_query"),
        InlineKeyboardButton(strings.menu.areas, callback_data="_areas"),
        InlineKeyboardButton(strings.menu.area_names, callback_data="_area_names"),
        InlineKeyboardButton(strings.menu.useful_links, callback_data="_useful_links"),
        InlineKeyboardButton(strings.menu.support, callback_data="_support"),
        InlineKeyboardButton(strings.menu.language, callback_data="_language"),
    )
    return menu_markup

def create_lang_menu_markup(strings):
    lang_menu_markup = InlineKeyboardMarkup(row_width=1)
    lang_menu_markup.add(
        InlineKeyboardButton(strings.language_en, callback_data="_en"),
        InlineKeyboardButton(strings.language_ru, callback_data="_ru")
    )
    return lang_menu_markup

def create_main_menu_button(strings):
    main_menu_button = InlineKeyboardMarkup(row_width=1)
    main_menu_button.add(InlineKeyboardButton(strings.main_menu, callback_data="_main_menu"))
    return main_menu_button

def create_create_query_menu(strings):
    query_menu = InlineKeyboardMarkup(row_width=2)
    query_menu.add(InlineKeyboardButton(strings.menu.area_names, callback_data="_area_names"))
    query_menu.add(InlineKeyboardButton(strings.main_menu, callback_data="_main_menu"))
    return query_menu

def create_areas_menu_markup(strings):
    areas_menu_markup = InlineKeyboardMarkup(row_width=1)
    areas_menu_markup.add(
        InlineKeyboardButton(strings.areas.dubai_marina, callback_data="_dubai_marina"),
        InlineKeyboardButton(strings.areas.business_bay, callback_data="_business_bay"),
        InlineKeyboardButton(strings.areas.downtown, callback_data="_downtown"),
        InlineKeyboardButton(strings.areas.creek_harbour, callback_data="_creek_harbour"),
        InlineKeyboardButton(strings.areas.sobha_hartland, callback_data="_sobha_hartland"),
        InlineKeyboardButton(strings.areas.city_walk, callback_data="_city_walk"),
        InlineKeyboardButton(strings.areas.enter_own_area, callback_data="_enter_own_area")
    )
    return areas_menu_markup

def register_handlers(bot):
    @bot.message_handler(commands=["start", "menu"])
    def menu_menu_command(message):

        user_id = message.from_user.id
        username = message.from_user.username

        # Check if user is in the channel
        if check_user_in_channel_sync(config.channel_name, username) is False:
            bot.send_message(
                message.chat.id,
                f"You need to join the channel @{config.channel_name} to use the bot."
            )
            return
        crud.upsert_user(user_id, username)

        user = crud.read_user(user_id)
        lang = user.language
        logger.info({"user_id": message.from_user.id, "message": message.text})

        bot.send_message(
            message.chat.id, strings[lang].start,
            reply_markup=create_main_menu_markup(strings[lang])
        )

    @bot.callback_query_handler(func=lambda call: call.data == "_main_menu")
    def main_menu_callback(call):
        user_id = call.from_user.id
        username = call.from_user.username

        user = crud.read_user(user_id)
        if not user:
            user = crud.upsert_user(user_id, username)

        lang = user.language
        logger.info({"user_id": user_id, "message": call.data})

        bot.send_message(
            call.message.chat.id, strings[lang].start,
            reply_markup=create_main_menu_markup(strings[lang])
        )

    # Language selection
    @bot.callback_query_handler(func=lambda call: call.data == "_language")
    def language(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        logger.info({"user_id": call.from_user.id, "message": call.data})

        lang_menu_markup = create_lang_menu_markup(strings[lang])
        bot.send_message(call.message.chat.id, "Language", reply_markup=lang_menu_markup)

    @bot.callback_query_handler(func=lambda call: call.data == "_ru")
    def language_ru(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        username = call.from_user.username
        lang = "ru"
        crud.update_user_language(user_id, new_language=lang)

        bot.send_message(
            call.message.chat.id, strings[lang].language_selected,
            reply_markup=create_main_menu_button(strings[lang])
        )

    @bot.callback_query_handler(func=lambda call: call.data == "_en")
    def language_en(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        username = call.from_user.username

        lang = "en"
        crud.update_user_language(user_id, new_language=lang)

        bot.send_message(
            call.message.chat.id, strings[lang].language_selected,
            reply_markup=create_main_menu_button(strings[lang])
        )


    # Useful links
    @bot.callback_query_handler(func=lambda call: call.data == "_useful_links")
    def useful_links(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].useful_links,
            reply_markup=create_main_menu_button(strings[lang])
        )

    # Help
    @bot.callback_query_handler(func=lambda call: call.data == "_support")
    def support(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        bot.send_message(call.message.chat.id, strings[lang].support,
            reply_markup=create_main_menu_button(strings[lang])
        )

    # Query
    @bot.callback_query_handler(func=lambda call: call.data == "_query")
    def query(call):
        logger.info({"user_id": call.from_user.id, "message": call.data})
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language
        bot.send_message(
            call.message.chat.id, strings[lang].query.ask_name,
            reply_markup=create_main_menu_button(strings[lang])
        )

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
            reply_markup=create_areas_menu_markup(strings[lang])
        )

    # Specific area handlers (e.g., for "Dubai Marina")
    @bot.callback_query_handler(func=lambda call: call.data in ["_dubai_marina", "_business_bay", "_downtown", "_creek_harbour", "_sobha_hartland", "_city_walk"])
    def area_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        area_name = call.data[1:].replace("_", " ").title()  # Format the area name from the callback data
        building_data = crud.get_buildings_by_area(area_name)

        # Create a pandas DataFrame from the sorted data
        df = pd.DataFrame(building_data)

        # Define the filename for the Excel file
        filename = f"{area_name}_buildings.xlsx"
        filepath = os.path.join("/tmp", filename)  # Save it to a temporary directory


        # Save the DataFrame to a local Excel file
        df.to_excel(filepath, index=False)

        # Send the Excel file to the user
        with open(filepath, 'rb') as file:
            bot.send_document(call.message.chat.id, file, reply_markup=create_main_menu_button(strings[lang]))

        # Delete the Excel file after sending it
        os.remove(filepath)

    # Handle the option where the user enters their own area name
    @bot.callback_query_handler(func=lambda call: call.data == "_enter_own_area")
    def enter_own_area_callback(call):
        msg = bot.send_message(call.message.chat.id, strings.en.areas.enter_own_area)
        bot.register_next_step_handler(msg, process_area_name)

    def process_area_name(message):
        user_id = message.from_user.id
        area_name = message.text
        user = crud.read_user(user_id)
        lang = user.language
        print(area_name)
        building_data = crud.get_buildings_by_area(area_name)
        if building_data:
            # Create a pandas DataFrame from the sorted data
            df = pd.DataFrame(building_data)

            # Define the filename for the Excel file
            filename = f"{area_name}_buildings.xlsx"
            filepath = os.path.join("/tmp", filename)  # Save it to a temporary directory


            # Save the DataFrame to a local Excel file
            df.to_excel(filepath, index=False)

            # Send the Excel file to the user
            with open(filepath, 'rb') as file:
                bot.send_document(user_id, file, reply_markup=create_main_menu_button(strings[lang]))

            # Delete the Excel file after sending it
            os.remove(filepath)
        else:
            bot.send_message(message.chat.id, f"No buildings found for {area_name}.", reply_markup=create_main_menu_button(strings[lang]))