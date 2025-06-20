import logging
import os
import re

from omegaconf import OmegaConf
from pydrive2.drive import GoogleDriveFile
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from real_estate_telegram_bot.api.handlers.apps.menu import create_main_menu_button
from real_estate_telegram_bot.core.google import GoogleDriveService
from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.db.models import ProjectFile

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/apps/query_files.yaml")
strings = config.strings

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize Google Drive service
google_drive_service = GoogleDriveService()


def create_query_results_buttons(results: list[str], lang: str) -> InlineKeyboardMarkup:
    buttons_markup = InlineKeyboardMarkup(row_width=1)
    for result in results:
        buttons_markup.add(InlineKeyboardButton(result, callback_data=f"_files_{result}"[:64]))
    buttons_markup.add(InlineKeyboardButton(
        strings[lang].keyword_search,
        callback_data=f"_keyword_search"
        )
    )
    return buttons_markup

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

def send_files(items: list[ProjectFile], user_id, bot) -> None:
    for item in items:

        file_name = item.file_name
        project_id = item.project_id

        # Check that file_name has a file extension
        if not re.search(r"\.\w+$", file_name):
            file_name += ".pdf"

        # Check if the file is already in the database
        project_file = crud.get_project_file_by_name(item.file_name)
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


def send_project_files(items: list[dict], project_id: int, user_id, bot) -> None:
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


def register_handlers(bot):
    """ Register handlers for the `query_files` command """
    logger.info("Registering `query_files` handlers")

    @bot.callback_query_handler(func=lambda call: "_query_files" in call.data)
    def docs_query_handler(call, data: dict):
        user = data["user"]
        bot.send_message(user.id, config.strings[user.lang].enter_project_name)
        bot.register_next_step_handler(call.message, perform_query, user)

    def perform_query(message, user):
        user_id = message.from_user.id
        project_name = message.text

        try:
            projects = crud.query_projects_by_name(project_name, mode="ilike")

            if projects:
                if len(projects) == 1:
                    google_drive_files = query_files_from_folder(projects[0].project_name_id_buildings)
                    if google_drive_files:
                        bot.send_message(
                            user_id,
                            strings[user.lang].files_found.format(n=len(google_drive_files))
                        )
                        send_project_files(
                            google_drive_files, user_id=user_id, bot=bot,
                            project_id=projects[0].project_id
                        )
                    else:
                        logger.info(f"No files found for project {projects[0].project_name_id_buildings}")
                        projects_buttons = create_query_results_buttons(
                            [], lang=user.lang
                        )
                    bot.reply_to(message, strings[user.lang].result_positive_suggestions, reply_markup=projects_buttons)
                else:
                    projects_buttons = create_query_results_buttons(
                        [project.project_name_id_buildings for project in projects],
                        lang=user.lang
                    )
                    bot.reply_to(
                        message, strings[user.lang].result_positive_suggestions,
                        reply_markup=projects_buttons
                    )
            else:
                projects = crud.query_projects_by_name(
                    project_name, mode="cosine",
                    similarity_threshold=config.app.similarity_threshold
                )
                if projects:
                    projects_buttons = create_query_results_buttons(
                        [project.project_name_id_buildings for project in projects][:config.app.top_k],
                        lang=user.lang
                    )
                    bot.reply_to(message, strings[user.lang].result_positive_suggestions, reply_markup=projects_buttons)
                else:
                    bot.reply_to(
                        message, strings[user.lang].result_negative,
                        reply_markup=create_main_menu_button(user.lang)
                    )
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    @bot.callback_query_handler(func=lambda call: "_files_" in call.data)
    def show_selected_project(call, data):
        user = data["user"]
        project_name = call.data.replace("_files_", "")
        projects = crud.query_projects_by_name(project_name)
        project = [project for project in projects if project.project_name_id_buildings == project_name][0]
        items = query_files_from_folder(project_name)
        if items:
            bot.send_message(user.id, config.strings[user.lang].files_found.format(n=len(items)))
            send_project_files(
                items, user_id=user.id, bot=bot,
                project_id=project.project_id
            )
        else:
            logger.info(f"No files found for project {project_name}")
            bot.send_message(user.id, config.strings[user.lang].no_files_found)

    @bot.callback_query_handler(func=lambda call: call.data == "_keyword_search")
    def keyword_search(call, data):
        user = data["user"]
        bot.send_message(user.id, strings[user.lang].enter_keyword)
        bot.register_next_step_handler(call.message, perform_keyword_search, user)

    def perform_keyword_search(message, user):
        user_id = message.from_user.id
        keyword = message.text
        project_files = crud.get_project_files_by_name(keyword)
        if project_files:
            bot.send_message(user_id, strings[user.lang].files_found.format(n=len(project_files)))
            for project_file in project_files:

                google_file = google_drive_service.get_file_by_title(project_file.file_name)

                if google_file is None:
                    logger.info(f"File {project_file.file_name} not found in Google Drive")

                    # try without extension
                    google_file = google_drive_service.get_file_by_title(project_file.file_name.split(".")[0])

                    if google_file is None:
                        logger.info(f"File {project_file.file_name.split('.')[0]} not found in Google Drive")
                        continue

                # Download the file from Google Drive
                google_drive_service.download_files(google_file, "./tmp")

                # Send the downloaded file to the user
                with open(f"./tmp/{google_file['title']}", 'rb') as file:
                    sent_message = bot.send_document(user_id, file)
                    # Add the file to the database
                    crud.add_project_file(
                        project_id=project_file.project_id,
                        file_name=project_file.file_name,
                        file_type="pdf",
                        file_telegram_id=sent_message.document.file_id
                    )

                # Remove file
                os.remove(f"./tmp/{google_file['title']}")

        else:
            bot.reply_to(
                message, strings[user.lang].result_negative,
                reply_markup=create_main_menu_button(user.lang)
            )
