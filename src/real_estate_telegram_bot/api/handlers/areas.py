import logging.config
import os

import pandas as pd
from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.core import excel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/apps/areas.yaml").strings

def create_areas_menu_markup(lang: str) -> InlineKeyboardMarkup:
    query_menu = InlineKeyboardMarkup(row_width=2)
    options = strings[lang].menu.options
    for option in options:
        query_menu.add(
            InlineKeyboardButton(option.label, callback_data=option.value)
        )
    return query_menu

def create_main_menu_button(lang: str):
    main_menu_button = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    main_menu_button.add(KeyboardButton(strings[lang].main_menu))
    return main_menu_button

def create_query_menu(lang: str) -> InlineKeyboardMarkup:
    query_menu = InlineKeyboardMarkup(row_width=2)
    query_menu.add(
        InlineKeyboardButton(strings[lang].query, callback_data="_query")
    )
    return query_menu

def create_areas_names_menu_markup(lang):
    areas = [
        ('al_furjan', strings.area_names.al_furjan),
        ('arjan', strings.area_names.arjan),
        ('beachfront', strings.area_names.beachfront),
        ('bluewaters', strings.area_names.bluewaters),
        ('business_bay', strings.area_names.business_bay),
        ('city_walk', strings.area_names.city_walk),
        ('creek_harbour', strings.area_names.creek_harbour),
        ('downtown', strings.area_names.downtown),
        ('dubai_hills', strings.area_names.dubai_hills),
        ('dubai_islands', strings.area_names.dubai_islands),
        ('dubai_marina', strings.area_names.dubai_marina),
        ('dubai_maritime_city', strings.area_names.dubai_maritime_city),
        ('jlt', strings.area_names.jlt),
        ('jvc', strings.area_names.jvc),
        ('jvt', strings.area_names.jvt),
        ('jbr', strings.area_names.jbr),
        ('la_mer', strings.area_names.la_mer),
        ('mina_rashid', strings.area_names.mina_rashid),
        ('palm_jumeirah', strings.area_names.palm_jumeirah),
        ('sobha_hartland', strings.area_names.sobha_hartland),
    ]
    areas_menu_markup = InlineKeyboardMarkup(row_width=2)
    for area_code, area_label in areas:
        areas_menu_markup.add(InlineKeyboardButton(area_label, callback_data=f"_{area_code}"))
    areas_menu_markup.add(
        InlineKeyboardButton(strings[lang].enter_own_area, callback_data="_enter_own_area")
    )
    return areas_menu_markup

def register_handlers(bot):
    """ Register handlers for areas menu """
    logger.info("Registering `areas` handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "_areas")
    def get_areas_menu(call, data: dict):
        user = data["user"]
        lang = user.lang

        logger.info({"user_id": user.id, "message": call.data})

        bot.send_message(
            call.message.chat.id,
            strings[lang].menu.title,
            reply_markup=create_areas_menu_markup(lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "buildings_area")
    def areas_menu_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.lang

        logger.info({"user_id": user_id, "message": call.data})

        bot.send_message(
            call.message.chat.id,
            strings[lang].select_area,
            reply_markup=create_areas_names_menu_markup(lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "area_names")
    def get_area_names_table(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.lang

        logger.info({"user_id": user_id, "message": call.data})

        with open("./data/dubai_area_names.xlsx", 'rb') as file:
            bot.send_document(user_id, file, reply_markup=create_main_menu_button(lang))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("_") and call.data[1:] in get_valid_area_codes())
    def area_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.lang

        area_code = call.data[1:]
        area_name = map_area_code_to_name(area_code)

        send_area_buildings(bot, user_id, area_name, lang)

    @bot.callback_query_handler(func=lambda call: call.data == "_enter_own_area")
    def enter_own_area_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.lang

        msg = bot.send_message(call.message.chat.id, strings[lang].enter_own_area)
        bot.register_next_step_handler(msg, process_area_name)

    def process_area_name(message):
        user_id = message.from_user.id
        area_name = message.text.strip()
        user = crud.read_user(user_id)
        lang = user.lang

        send_area_buildings(bot, user_id, area_name, lang, user_entered=True)

    def send_area_buildings(bot, user_id, area_name, lang, user_entered=False):
        logger.info(f"User {user_id} requested buildings in {area_name}")
        building_data = crud.get_buildings_by_area(area_name)
        if building_data:
            df = pd.DataFrame(building_data)
            df = df.sort_values(by='Construction end date', ascending=False)
            df['Construction end date'] = df['Construction end date'].dt.strftime('%d-%m-%Y')

            masks = {
                'ready': df['Completion %'] == 100,
                'off_plan': df['Completion %'] != 100
            }

            for name, mask in masks.items():
                if df[mask].empty:
                    continue

                filename = f"{area_name}_buildings_{name}.xlsx"
                filepath = os.path.join("./tmp", filename)

                df[mask].to_excel(filepath, index=False)
                excel.format_areas(filepath)

                with open(filepath, 'rb') as file:
                    reply_markup = create_query_menu(lang) if name == 'off_plan' else None
                    bot.send_document(user_id, file, reply_markup=reply_markup)

                os.remove(filepath)
        else:
            bot.send_message(
                user_id,
                strings[lang].area_query.result_negative,
                reply_markup=create_query_menu(lang)
            )

    def get_valid_area_codes():
        return [
            'al_furjan', 'arjan', 'beachfront', 'bluewaters', 'business_bay', 'city_walk',
            'creek_harbour', 'downtown', 'dubai_hills', 'dubai_islands', 'dubai_marina',
            'dubai_maritime_city', 'jlt', 'jvc', 'jvt', 'jbr', 'la_mer', 'mina_rashid',
            'palm_jumeirah', 'sobha_hartland'
        ]

    def map_area_code_to_name(area_code):
        special_cases = {
            'jlt': 'Jumeirah Lakes Towers',
            'jvc': 'Jumeirah Village Circle',
            'jvt': 'Jumeirah Village Triangle',
            'jbr': 'Jumeriah Beach Residence'
        }
        return special_cases.get(area_code, area_code.replace('_', ' ').title())
