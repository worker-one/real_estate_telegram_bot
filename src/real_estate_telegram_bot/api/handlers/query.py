import datetime
import logging
import os
import re

from omegaconf import OmegaConf
from pydrive2.drive import GoogleDriveFile
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from real_estate_telegram_bot.api.handlers.menu import create_main_menu_button
from real_estate_telegram_bot.api.users import check_user_in_channel_sync
from real_estate_telegram_bot.core.google import GoogleDriveService
from real_estate_telegram_bot.db import crud

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/apps/query.yaml").app
strings = OmegaConf.load("./src/real_estate_telegram_bot/conf/apps/query.yaml").strings
config_common = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

google_drive_service = GoogleDriveService()

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
    # if formatted_project_json['construction_duration'] != 'N/A':
    #     formatted_project_json['construction_duration'] += " years"
    if formatted_project_json['project_age'] != "Under construction":
        formatted_project_json['project_age'] += " years"

    return template.format(**formatted_project_json).strip()

def create_service_charge_button(lang: str, master_community_name_en: str):
    service_charge_button = InlineKeyboardMarkup(row_width=2)
    service_charge_button.add(
        InlineKeyboardButton(strings[lang].service_charge, callback_data=f"_service_charge_{master_community_name_en}")
    )
    return service_charge_button

def create_query_results_buttons(results: list[str]) -> InlineKeyboardMarkup:
    buttons_markup = InlineKeyboardMarkup(row_width=1)
    for result in results:
        buttons_markup.add(InlineKeyboardButton(result, callback_data=f"_select_{result}"[:64]))
    return buttons_markup

def create_query_files_button(lang: str) -> InlineKeyboardMarkup:
    query_files_button = InlineKeyboardMarkup(row_width=2)
    query_files_button.add(
        InlineKeyboardButton(strings[lang].query_files, callback_data=f"_query_files")
    )
    return query_files_button


def query_files_from_folder(folder_name: str) -> list[GoogleDriveFile]:
    """   Query files from a specific folder in Google Drive.

    Args:
        folder_name (str): The name of the folder in Google Drive.
    Returns:
        A list of files in the folder.
    """
    folder_id = google_drive_service.get_folder_id(folder_name.strip())
    drive_files = google_drive_service.list_files_in_folder(folder_id)
    return drive_files


def send_files(items: list[GoogleDriveFile], project_id: int, user_id, bot) -> None:
    for item in items:
        file_name = item['title']

        # Check that file_name has a file extension
        if not re.search(r"\.\w+$", file_name):
            file_name += ".pdf"

        # Check if the file is already in the database
        project_file = crud.get_project_file_by_name(file_name)
        if not project_file:
            logger.info(f"Downloading file {file_name} from Google Drive")

            # Download the file from Google Drive
            google_drive_service.download_files(item, "./tmp")

            # Send the downloaded file to the user
            with open(f"./tmp/{file_name}", 'rb') as file:
                sent_message = bot.send_document(user_id, file)
                # Add the file to the database
                crud.add_project_file(
                    project_id=project_id,
                    file_name=file_name,
                    file_type="pdf",
                    file_telegram_id=sent_message.document.file_id
                )

            # Remove file
            os.remove(f"./tmp/{file_name}")
        else:
            logger.info(f"File {file_name} already exists in the database")
            try:
                bot.send_document(user_id, project_file.file_telegram_id)
            except Exception as e:
                logger.error(f"An error occurred: {e}")

                # Download the file from Google Drive
                google_drive_service.download_files(item, "./tmp")

                # Send the downloaded file to the user
                with open(f"./tmp/{file_name}", 'rb') as file:
                    sent_message = bot.send_document(user_id, file)
                    # Add the file to the database
                    crud.update_project_file(
                        project_id=project_id,
                        file_name=file_name,
                        file_type="pdf",
                        file_telegram_id=sent_message.document.file_id
                    )
                    logger.info(f"File {file_name} updated in the database")

                # Remove file
                os.remove(f"./tmp/{file_name}")

def is_query(message):
    is_command = message.text[0] == '/'
    is_key_phrase = message.text in {
        strings["en"].main_menu,
        strings["ru"].main_menu
    }
    return not is_command and not is_key_phrase

def register_handlers(bot):
    @bot.message_handler(Command="query")
    def query_handler(message):
        user_id = message.from_user.id
        user = crud.read_user(user_id)
        lang = user.lang
        bot.reply_to(message, strings[lang].ask_name,
            reply_markup=create_main_menu_button(lang))
        bot.register_next_step_handler(message, perform_query)

    @bot.message_handler(func=lambda message: is_query(message))
    def perform_query(message):
        user_id = message.from_user.id
        username = message.from_user.username

        # Check if user is in the channel
        if config_common.app.restrict_access:
            if check_user_in_channel_sync(config_common.channel_name, username) is False:
                bot.send_message(
                    message.chat.id,
                    f"You need to join the channel @{config_common.channel_name} to use the bot."
                )
                return

        user = crud.read_user(user_id)
        lang = user.lang
        project_name = message.text

        logger.info(msg="User event", extra={"user_id": user_id, "user_message": message.text})
        try:
            projects = crud.query_projects_by_name(project_name, mode="ilike")

            if projects:
                if len(projects) == 1:
                    bot.reply_to(message, strings[lang].result_positive_unique)
                    bot.send_message(
                        user_id, prepare_response(projects[0]),
                        parse_mode="Markdown",
                        reply_markup=create_service_charge_button(lang, projects[0].master_project_en)
                    )
                    items = query_files_from_folder(projects[0].project_name_id_buildings)
                    if items:
                        bot.send_message(user_id, strings[lang].files_found.format(n=len(items)))
                        send_files(
                            items, user_id=user_id, bot=bot,
                            project_id=projects[0].project_id
                        )
                    else:
                        logger.info(f"No files found for project {projects[0].project_name_id_buildings}")
                        bot.send_message(
                            user_id, strings[lang].no_media_found,
                            reply_markup=create_query_files_button(lang)
                        )
                else:
                    projects_buttons = create_query_results_buttons(
                        [project.project_name_id_buildings for project in projects]
                    )
                    bot.reply_to(message, strings[lang].result_positive_nonunique, reply_markup=projects_buttons)
                    #bot.register_next_step_handler(message, show_selected_project)
            else:

                projects = crud.query_projects_by_name(project_name, mode="cosine", similarity_threshold=config.similarity_threshold)
                if projects:
                    projects_buttons = create_query_results_buttons(
                        [project.project_name_id_buildings for project in projects][:config.top_k]
                    )
                    bot.reply_to(message, strings[lang].result_positive_suggestions, reply_markup=projects_buttons)
                else:
                    bot.reply_to(
                        message, strings[lang].result_negative,
                        reply_markup=create_main_menu_button(lang)
                    )
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            bot.reply_to(
                message, strings[lang].result_negative,
                reply_markup=create_main_menu_button(lang)
            )

    @bot.callback_query_handler(func=lambda call: "_select_" in call.data)
    def show_selected_project(call):
        logger.info(msg="User event", extra={"user_id": call.from_user.id, "user_message": call.data})
        project_name = call.data.replace("_select_", "")
        user_id = call.from_user.id
        user = crud.read_user(user_id)
        lang = user.lang

        projects = crud.query_projects_by_name(project_name)
        project = [project for project in projects if project.project_name_id_buildings == project_name][0]
        bot.send_message(
            user_id, prepare_response(project).replace('_', " "),
            reply_markup=create_service_charge_button(lang, project.master_project_en),
            parse_mode="Markdown"
        )
        items = query_files_from_folder(project_name)
        if items:
            bot.send_message(user_id, strings[lang].files_found.format(n=len(items)))
            send_files(
                items, user_id=user_id, bot=bot,
                project_id=project.project_id
            )
        else:
            logger.info(f"No files found for project {project_name}")
            bot.send_message(
                user_id, strings[lang].no_media_found,
                reply_markup=create_query_files_button(lang)
            )
