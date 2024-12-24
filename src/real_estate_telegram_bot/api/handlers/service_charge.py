import logging
import os

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.core import excel

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/apps/service_charge.yaml")
strings = config.strings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_areas_names_menu_markup(lang):
    areas = [
        ('arjan', strings.area_names.arjan),
        ('beachfront', strings.area_names.beachfront),
        ('bluewaters', strings.area_names.bluewaters),
        ('business_bay', strings.area_names.business_bay),
        ('city_walk', strings.area_names.city_walk),
        ("damac_hills", strings.area_names.damac_hills),
        ('downtown', strings.area_names.downtown),
        ('dubai_hills', strings.area_names.dubai_hills),
        ('dubai_marina', strings.area_names.dubai_marina),
        ('dubai_maritime_city', strings.area_names.dubai_maritime_city),
        ('jlt', strings.area_names.jlt),
        ('jvc', strings.area_names.jvc),
        ('jvt', strings.area_names.jvt),
        ('jbr', strings.area_names.jbr),
        ('mjl', strings.area_names.mjl),
        ('palm_jumeirah', strings.area_names.palm_jumeirah),
        ('sobha_hartland', strings.area_names.sobha_hartland),
        ('creek_harbour', strings.area_names.creek_harbour),
    ]
    areas_menu_markup = InlineKeyboardMarkup(row_width=2)
    for area_code, area_label in areas:
        areas_menu_markup.add(InlineKeyboardButton(area_label, callback_data=f"_service_charge_{area_code}"))
    areas_menu_markup.add(
        InlineKeyboardButton(strings[lang].enter_own_area, callback_data="_enter_own_area_service_charge")
    )
    return areas_menu_markup

def create_main_menu_button(lang: str):
    main_menu_button = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    main_menu_button.add(KeyboardButton(strings[lang].main_menu))
    return main_menu_button

def register_handlers(bot):
    """ Register the service charge handlers """
    logger.info("Registering service charge handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "_service_charge")
    def show_service_charge(call, data: dict):
        user = data["user"]
        # Send the buttons to the user
        bot.send_message(
            user.id, strings[user.lang].select_area,
            reply_markup=create_areas_names_menu_markup(user.lang)
        )

    @bot.callback_query_handler(func=lambda call: "_enter_own_area_service_charge" == call.data)
    def enter_own_area_service_charge(call, data: dict):
        user = data["user"]
        lang = user.lang
        bot.send_message(user.id, strings[lang].enter_own_area)
        bot.register_next_step_handler_by_chat_id(user.id, get_service_charge, user)

    def get_service_charge(message, user):
        area_name = message.text
        df = crud.get_area_service_charge_by_year(area_name)
        if len(df) != 0:
            filename = f"{area_name}_service_charge.xlsx"
            filepath = os.path.join("./tmp", filename)
            df.to_excel(filepath, index=False)
            excel.format_service_charge(filepath, master_project_en=area_name, header_color="ed7d31")
            with open(filepath, 'rb') as file:
                bot.send_document(user.id, file, caption=strings[user.lang].result_positive)
            os.remove(filepath)
        else:
            bot.send_message(user.id, strings[user.lang].result_negative)

    @bot.callback_query_handler(func=lambda call: "_service_charge_" in call.data)
    def show_service_charge_for_project(call, data: dict):
        master_project_en = call.data.replace("_service_charge_", "").strip()

        user = data["user"]
        lang = user.lang

        df = crud.get_project_service_charge_by_year(master_project_en)

        if len(df) != 0:

            # Define the filename for the Excel file
            filename = f"{master_project_en}_service_charge.xlsx"
            filepath = os.path.join("./tmp", filename)  # Save it to a temporary directory

            # Save the DataFrame to a local Excel file
            df.to_excel(filepath, index=False)

            # Format the Excel file
            excel.format_service_charge(filepath, master_project_en=master_project_en, header_color="ed7d31")

            # Send the formatted Excel file to the user
            with open(filepath, 'rb') as file:
                bot.send_document(
                    user.id, file, caption=strings[lang].result_positive,
                    reply_markup=create_main_menu_button(lang)
                )

            # Delete the Excel file after sending it
            os.remove(filepath)
        else:
            bot.send_message(user.id, strings[lang].result_negative)
            bot.send_message(user.id, strings[lang].enter_own_area)
            bot.register_next_step_handler_by_chat_id(user.id, get_service_charge, user)
