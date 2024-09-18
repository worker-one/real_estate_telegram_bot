import math
import datetime
import yaml
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


def format_date(date):
    return date.strftime('%d.%m.%Y') if date else 'N/A'

def prepepare_response(project_json: dict) -> str:
    template = strings.project_info_template

    formatted_project_json = {
        'project_name_id_buildings': project_json['project_name_id_buildings'],
        'developer_name_en': project_json['developer_name_en'],
        'master_developer_name_en': project_json['master_developer_name_en'],
        'area_name_en': project_json['area_name_en'],
        'master_project_en': project_json['master_project_en'],
        'registration_date': format_date(project_json['registration_date']),
        'project_start_date': format_date(project_json['project_start_date']),
        'project_end_date': format_date(project_json['project_end_date']),
        'construction_duration': project_json.get('construction_duration', 'N/A'),
        'project_age': project_json.get('project_age', 'Under construction'),
        'project_status': project_json['project_status'],
        'percent_completed': project_json['percent_completed'],
        'no_of_buildings': project_json['no_of_buildings'],
        'no_of_units': project_json['no_of_units'],
        'floors': project_json['floors'],
        'is_free_hold': project_json['is_free_hold'],
        'project_description_en': project_json['project_description_en'],
        'license_source_en': project_json['license_source_en'],
        'license_number': project_json['license_number'],
        'license_issue_date': format_date(project_json['license_issue_date']),
        'license_expiry_date': format_date(project_json['license_expiry_date']),
        'webpage': project_json['webpage']
    }

    return template.format(**formatted_project_json).strip()

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

                # 
                if project_json['percent_completed'] != 100:
                    project_json['project_age'] = 'Under construction'

                bot.send_message(user_id, prepepare_response(project_json), parse_mode="markdown")
            bot.send_message(user_id, strings.query.result_positive_report)
        else:
            bot.reply_to(message, strings.query.result_negative)
