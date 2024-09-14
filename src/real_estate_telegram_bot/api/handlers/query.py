import datetime
import json
import logging

from omegaconf import OmegaConf
from real_estate_telegram_bot.db.crud import query_project_by_name


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
        project = query_project_by_name(project_name)

        if project:
            # jsonfy
            project_json = project.as_dict()
            if project.project_start_date and project.project_end_date:
                project_json['project_age'] = project.project_end_date - project.project_start_date
                project_json['project_age'] = str(project_json['project_age'].days)
            
            # convert all datetime objects to string
            for key, value in project_json.items():
                if isinstance(value, datetime.datetime):
                    project_json[key] = value.strftime('%Y-%m-%d')
                    
            # dump to json with indent
            project_json = json.dumps(project_json, indent=4, ensure_ascii=False)
            bot.reply_to(message, strings.query.result_positive)
            bot.send_message(user_id, f'```json\n{project_json}\n```', parse_mode="Markdown")
        else:
            bot.reply_to(message, strings.query.result_negative)
