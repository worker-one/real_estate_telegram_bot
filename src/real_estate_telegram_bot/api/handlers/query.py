import datetime
import logging
import os
import re

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from real_estate_telegram_bot.api.handlers.menu import create_main_menu_button
from real_estate_telegram_bot.api.users import check_user_in_channel_sync
from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.service.google import GoogleDriveAPI

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/strings.yaml")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

google_drive_api = GoogleDriveAPI()
google_drive_api.load_index()


def format_date(date):
    return date.strftime('%d.%m.%Y') if date else 'N/A'

def calculate_years_between(start_date, end_date) -> str:
    """Calculate the number of years between two dates, rounded to 1 decimal place."""
    duration = end_date - start_date
    return str(round(duration.days / 365.25, 1))

def prepare_response(project) -> str:
    project_json = project.as_dict()

    current_date = datetime.datetime.now()

    # Compute construction duration if start and end dates are provided
    if project.project_start_date and project.project_end_date:
        project_json['construction_duration'] = calculate_years_between(project.project_start_date, project.project_end_date)

    # Compute age of the project if the project is completed and its end date is in the past
    if project.project_end_date and current_date > project.project_end_date:
        project_json['project_age'] = calculate_years_between(project.project_end_date, current_date)

    # Handle under construction case
    if project_json['percent_completed'] != 100:
        project_json['project_age'] = 'Under construction'

    template = strings.project_info_template
    formatted_project_json = {
        'project_name_id_buildings': project_json['project_name_id_buildings'],
        'developer_name_en': project_json['developer_name_en'],
        #'master_developer_name_en': project_json['master_developer_name_en'],
        'area_name_en': project_json['area_name_en'],
        'master_project_en': project_json['master_project_en'],
        #'registration_date': format_date(project_json.get('registration_date')),
        'project_start_date': format_date(project_json.get('project_start_date')),
        'project_end_date': format_date(project_json.get('project_end_date')),
        #'construction_duration': project_json.get('construction_duration', 'N/A'),
        'project_age': project_json.get('project_age', 'Under construction'),
        'project_status': project_json['project_status'],
        'percent_completed': project_json['percent_completed'],
        'no_of_buildings': project_json['no_of_buildings'],
        'no_of_units': project_json['no_of_units'],
        'floors': project_json['floors'],
        'is_free_hold': project_json['is_free_hold'],
        # 'project_description_en': project_json['project_description_en'],
        # 'license_source_en': project_json['license_source_en'],
        # 'license_number': project_json['license_number'],
        # 'license_issue_date': format_date(project_json.get('license_issue_date')),
        # 'license_expiry_date': format_date(project_json.get('license_expiry_date')),
        # 'webpage': project_json['webpage']
    }


    # Append 'years' suffix where applicable
    if formatted_project_json['construction_duration'] != 'N/A':
        formatted_project_json['construction_duration'] += " years"
    if formatted_project_json['project_age'] != "Under construction":
        formatted_project_json['project_age'] += " years"

    return template.format(**formatted_project_json).strip()

def create_service_charge_button(strings: dict, master_community_name_en: str):
    service_charge_button = InlineKeyboardMarkup(row_width=1)
    service_charge_button.add(
        InlineKeyboardButton(strings.menu.service_charge, callback_data=f"_service_charge_{master_community_name_en}")
    )
    return service_charge_button

def create_query_results_buttons(results: list[str]) -> InlineKeyboardMarkup:
    buttons_markup = InlineKeyboardMarkup(row_width=1)
    for result in results:
        buttons_markup.add(InlineKeyboardButton(result, callback_data=f"_select_{result}"[:64]))
    return buttons_markup


def query_files(query: str, case_sensitive: bool = False):
    try:
        return google_drive_api.search(query.lower().strip(), case_sensitive=case_sensitive)
    except Exception as e:
        logger.info(f"An error occurred: {e}")
        return None


def send_files(items: list[dict], project_id: int, user_id, bot) -> None:
    for item in items:
        file_name = item['file_name']
        file_id = item['id']

        # Check that file_name has a file extension
        if not re.search(r"\.\w+$", file_name):
            file_name += ".pdf"

        # Check if the file is already in the database
        project_file = crud.get_project_file_by_name(item["file_name"])
        if not project_file:
            logger.info(f"Downloading file {file_name} from Google Drive")

            # Download the file from Google Drive
            google_drive_api.download_file(file_id, file_name)

            # Send the downloaded file to the user
            with open(file_name, 'rb') as file:
                sent_message = bot.send_document(user_id, file)
                # Add the file to the database
                crud.add_project_file(
                    project_id=project_id,
                    file_name=file_name,
                    file_type="pdf",
                    file_telegram_id=sent_message.document.file_id
                )

            # Remove file
            os.remove(file_name)
        else:
            logger.info(f"File {file_name} already exists in the database")
            bot.send_document(user_id, project_file.file_telegram_id)


def register_handlers(bot):
    @bot.message_handler(Command="query")
    def query_handler(message):
        user_id = message.from_user.id
        user = crud.read_user(user_id)
        lang = user.language
        logger.info(msg="User event", extra={"user_id": user_id, "user_message": message.text})
        bot.reply_to(message, strings[lang].query.ask_name,
            reply_markup=create_main_menu_button(strings[lang]))
        bot.register_next_step_handler(message, perform_query)

    @bot.message_handler(func=lambda message: message.text[0] != '/')
    def perform_query(message):
        user_id = message.from_user.id
        username = message.from_user.username


        # Check if user is in the channel
        if check_user_in_channel_sync(config.channel_name, username) is False:
            bot.send_message(
                message.chat.id,
                f"You need to join the channel @{config.channel_name} to use the bot."
            )
            return

        user = crud.read_user(user_id)
        lang = user.language
        project_name = message.text

        logger.info(msg="User event", extra={"user_id": user_id, "user_message": message.text})
        try:
            projects = crud.query_projects_by_name(project_name)

            if projects:
                if len(projects) == 1:
                    print(projects)
                    bot.reply_to(message, strings[lang].query.result_positive_unique)
                    bot.send_message(
                        user_id, prepare_response(projects[0]),
                        parse_mode="Markdown",
                        reply_markup=create_service_charge_button(strings[lang], projects[0].area_name_en)
                    )
                    bot.send_message(
                        user_id, strings[lang].query.result_positive_report,
                        reply_markup=create_main_menu_button(strings[lang])
                        )
                    items = query_files(projects[0].project_name_id_buildings)
                    if items:
                        bot.send_message(user_id, strings[lang].query.files_found.format(n=len(items)))
                        send_files(
                            items, user_id=user_id, bot=bot,
                            project_id=projects[0].project_id
                        )
                    else:
                        bot.send_message(user_id, strings[lang].query.files_not_found)
                else:
                    projects_buttons = create_query_results_buttons(
                        [project.project_name_id_buildings for project in projects]
                    )
                    bot.reply_to(message, strings[lang].query.result_positive_nonunique, reply_markup=projects_buttons)
                    #bot.register_next_step_handler(message, show_selected_project)
            else:
                bot.reply_to(
                    message, strings[lang].query.result_negative,
                    reply_markup=create_main_menu_button(strings[lang])
                )
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            bot.reply_to(
                message, strings[lang].query.result_negative,
                reply_markup=create_main_menu_button(strings[lang])
            )

    @bot.callback_query_handler(func=lambda call: "_select_" in call.data)
    def show_selected_project(call):
        logger.info(msg="User event", extra={"user_id": call.from_user.id, "user_message": call.data})
        project_id = call.data.replace("_select_", "")
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.language

        projects = crud.query_projects_by_name(project_id)
        project = [project for project in projects if project.project_name_id_buildings == project_id][0]
        bot.send_message(
            user_id, prepare_response(project).replace('_', " "),
            parse_mode="Markdown"
        )
        items = query_files(project_id)
        if items:
            bot.send_message(user_id, strings[lang].query.files_found.format(n=len(items)))
            send_files(
                items, user_id=user_id, bot=bot,
                project_id=project_id
            )
        bot.send_message(
            user_id, strings[lang].query.result_positive_report,
            reply_markup=create_main_menu_button(strings[lang])
        )
