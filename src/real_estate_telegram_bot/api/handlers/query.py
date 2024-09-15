import math
import datetime
import json
import logging

from omegaconf import OmegaConf
from real_estate_telegram_bot.db.crud import query_projects_by_name
from real_estate_telegram_bot.db.models import Project

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
lang = config.lang
strings = config.strings[lang]

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/real_estate_telegram_bot/conf/logging_config.yaml"),
    resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

def prepepare_response(project_json: dict) -> str:
    project_info = f"""
    **Project information**:

    Project: {project_json['project_name']} ({project_json['project_name_id_buildings']})
    Developer: {project_json['developer_name_en']}
    Master developer: {project_json['master_developer_name_en']}
    Area (Arabic): {project_json['area_name_en']}
    Area (English): {project_json['master_project_en']}
    Project registration date: {project_json['registration_date'].strftime('%d.%m.%Y') if project_json['registration_date'] else 'N/A'}
    Project start date: {project_json['project_start_date'].strftime('%d.%m.%Y') if project_json['project_start_date'] else 'N/A'}
    Project end date: {project_json['project_end_date'].strftime('%d.%m.%Y') if project_json['project_end_date'] else 'N/A'}
    Construction duration (up to date): {project_json.get('construction_duration', 'N/A')} (Лет)
    How old is the building: {project_json.get('project_age', 'N/A')} (Количество лет зданию)
    Project status: {project_json['project_status']}
    Completion: {project_json['percent_completed']}% 
    Number of buildings: {project_json['no_of_buildings']}
    Number of units: {project_json['no_of_units']}
    Number of floors: {project_json['floors']}
    Freehold: {project_json['is_free_hold']}
    Project description: {project_json['project_description_en']}

    **Developer information**:

    Developer license information
    Developer registration date: {project_json['registration_date'].strftime('%d.%m.%Y') if project_json['registration_date'] else 'N/A'}
    License source: {project_json['license_source_en']}
    Licence number: {project_json['license_number']}
    Issue date: {project_json['license_issue_date'].strftime('%d.%m.%Y') if project_json['license_issue_date'] else 'N/A'}
    Expiry date: {project_json['license_expiry_date'].strftime('%d.%m.%Y') if project_json['license_expiry_date'] else 'N/A'}
    Web-site: {project_json['webpage']}
    """
    return project_info.strip()

def register_handlers(bot):
    @bot.message_handler(commands=['query'])
    def query_handler(message):
        logger.info(f"Received query command from user {message.from_user.id}")
        bot.reply_to(message, strings.query.ask_name)
        bot.register_next_step_handler(message, perform_query)

    def perform_query(message):
        user_id = message.from_user.id
        project_name = message.text

        logger.info(f"User {message.from_user.id} queried for project: {project_name}")
        projects = query_projects_by_name(project_name)

        if projects:
            if len(projects) == 1:
                bot.reply_to(message, strings.query.result_positive_unique)
            if len(projects) > 1:
                bot.reply_to(message, strings.query.result_positive_nonunique)
            for project in projects:
                project_json = project.as_dict()

                # compute construction duration
                if project.project_start_date and project.project_end_date:
                    project_json['construction_duration'] = project.project_end_date - project.project_start_date
                    project_json['construction_duration'] = str(math.ceil((project_json['construction_duration'].days / 365.25) * 10) / 10)

                # compute age of the project
                if project.project_end_date and datetime.datetime.now() > project.project_end_date:
                    project_json['project_age'] = datetime.datetime.now() - project.project_end_date
                    project_json['project_age'] = str(math.ceil((project_json['project_age'].days / 365.25) * 10) / 10)

                bot.send_message(user_id, prepepare_response(project_json), parse_mode="markdown")
            bot.send_message(user_id, strings.query.result_positive_report)
        else:
            bot.reply_to(message, strings.query.result_negative)
