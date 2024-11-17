import logging.config
import os

import pandas as pd
from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.service import excel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/strings.yaml")

def create_main_menu_button(strings):
    main_menu_button = InlineKeyboardMarkup(row_width=1)
    main_menu_button.add(InlineKeyboardButton(strings.main_menu, callback_data="_main_menu"))
    return main_menu_button

def create_query_menu(strings):
    query_menu = InlineKeyboardMarkup(row_width=2)
    query_menu.add(
        InlineKeyboardButton(strings.menu.query, callback_data="_query"),
        InlineKeyboardButton(strings.main_menu, callback_data="_main_menu")
    )
    return query_menu

def create_areas_menu_markup(strings, lang):
    areas = [
        ('al_furjan', strings.areas.al_furjan),
        ('arjan', strings.areas.arjan),
        ('beachfront', strings.areas.beachfront),
        ('bluewaters', strings.areas.bluewaters),
        ('business_bay', strings.areas.business_bay),
        ('city_walk', strings.areas.city_walk),
        ('creek_harbour', strings.areas.creek_harbour),
        ('downtown', strings.areas.downtown),
        ('dubai_hills', strings.areas.dubai_hills),
        ('dubai_islands', strings.areas.dubai_islands),
        ('dubai_marina', strings.areas.dubai_marina),
        ('dubai_maritime_city', strings.areas.dubai_maritime_city),
        ('jlt', strings.areas.jlt),
        ('jvc', strings.areas.jvc),
        ('jvt', strings.areas.jvt),
        ('jbr', strings.areas.jbr),
        ('la_mer', strings.areas.la_mer),
        ('mina_rashid', strings.areas.mina_rashid),
        ('palm_jumeirah', strings.areas.palm_jumeirah),
        ('sobha_hartland', strings.areas.sobha_hartland),
    ]
    areas_menu_markup = InlineKeyboardMarkup(row_width=2)
    for area_code, area_label in areas:
        areas_menu_markup.add(InlineKeyboardButton(area_label, callback_data=f"_{area_code}"))
    areas_menu_markup.add(
        InlineKeyboardButton(strings[lang].query.enter_own_area, callback_data="_enter_own_area")
    )
    return areas_menu_markup

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "_area_names")
    def get_area_names_table(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        logger.info({"user_id": user_id, "message": call.data})

        with open("./data/dubai_area_names.xlsx", 'rb') as file:
            bot.send_document(user_id, file, reply_markup=create_main_menu_button(strings[lang]))

    @bot.callback_query_handler(func=lambda call: call.data == "_areas")
    def areas_menu_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        logger.info({"user_id": user_id, "message": call.data})

        bot.send_message(
            call.message.chat.id,
            strings[lang].menu.select_area,
            reply_markup=create_areas_menu_markup(strings, lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("_") and call.data[1:] in get_valid_area_codes())
    def area_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        area_code = call.data[1:]
        area_name = map_area_code_to_name(area_code)

        send_area_buildings(bot, user_id, area_name, lang)

    @bot.callback_query_handler(func=lambda call: call.data == "_enter_own_area")
    def enter_own_area_callback(call):
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        msg = bot.send_message(call.message.chat.id, strings[lang].query.enter_own_area)
        bot.register_next_step_handler(msg, process_area_name)

    def process_area_name(message):
        user_id = message.from_user.id
        area_name = message.text.strip()
        user = crud.read_user(user_id)
        lang = user.language

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
                    reply_markup = create_query_menu(strings[lang]) if name == 'off_plan' else None
                    bot.send_document(user_id, file, reply_markup=reply_markup)

                os.remove(filepath)
        else:
            bot.send_message(
                user_id,
                strings[lang].area_query.result_negative,
                reply_markup=create_query_menu(strings[lang])
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
