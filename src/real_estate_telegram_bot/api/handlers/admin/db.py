import logging
import logging.config
import os
from datetime import datetime

from telebot.handler_backends import State, StatesGroup
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from omegaconf import OmegaConf
from real_estate_telegram_bot.db import crud
from real_estate_telegram_bot.core.db import import_projects_from_excel, import_service_charges_from_excel

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
app_config = OmegaConf.load("./src/real_estate_telegram_bot/conf/admin/db.yaml")
strings = app_config.strings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImportStates(StatesGroup):
    waiting_for_table = State()
    waiting_for_file = State()


def register_handlers(bot):
    logger.info("Registering admin database handler")

    @bot.callback_query_handler(func=lambda call: call.data == "export_data")
    def export_data_handler(call, data):
        user = data["user"]

        if user.role != "admin":
            # inform that the user does not have rights
            bot.send_message(call.from_user.id, strings[user.lang].no_rights)
            return

        # Export data
        export_dir = f'./data/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(export_dir)
        try:
            crud.export_all_tables(export_dir)
            for table in config.db.tables:
                # save as excel in temp folder and send to a user
                filename = f"{export_dir}/{table}.csv"
                bot.send_document(user.id, open(filename, "rb"))
                # remove the file
                os.remove(filename)
        except Exception as e:
            bot.send_message(user.id, str(e))
            logger.error(f"Error exporting data: {e}")

    @bot.callback_query_handler(func=lambda call: call.data == "import_data")
    def import_data_handler(call, data):
        user = data["user"]
        
        if user.role != "admin":
            bot.send_message(call.from_user.id, strings[user.lang].no_rights)
            return

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Projects", callback_data="import_projects"),
            InlineKeyboardButton("Service Charges", callback_data="import_service_charges")
        )
        bot.send_message(call.from_user.id, strings[user.lang].select_table_to_import, reply_markup=markup)
        
        data["state"].set(ImportStates.waiting_for_table)

    @bot.callback_query_handler(func=lambda call: call.data in ["import_projects", "import_service_charges"])
    def handle_table_selection(call, data):
        user = data["user"]
        bot.send_message(call.from_user.id, strings[user.lang].please_upload_excel_file)
        
        data["state"].add_data(table_type=call.data)
        data["state"].set(call, ImportStates.waiting_for_file)

    @bot.message_handler(content_types=['document'])
    def handle_file(message, data):
        user = data["user"]

        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            temp_file = f'./data/temp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            with open(temp_file, 'wb') as f:
                f.write(downloaded_file)

            with data["state"].data() as data_items:
                table_type = data_items["table_type"]
            
            bot.send_message(message.chat.id, strings[user.lang].please_wait)
            if table_type == "import_projects":
                results_df = import_projects_from_excel(temp_file)
            else:
                results_df = import_service_charges_from_excel(temp_file)
            
            # Log summary
            total = len(results_df)
            created = len(results_df[results_df['status'] == 'created'])
            updated = len(results_df[results_df['status'] == 'updated'])
            errors = len(results_df[results_df['status'] == 'error'])
            success_msg = strings[user.lang].processed_records.format(total=total, created=created, updated=updated, errors=errors)
            
            # Save results_df as excel file
            results_file = f'./data/results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            results_df.to_excel(results_file, index=False)
            
            bot.send_message(message.chat.id, success_msg)
            # send a document
            with open(results_file, 'rb') as f:
                bot.send_document(message.chat.id, f)
            data["state"].delete()
            
            os.remove(temp_file)
            os.remove(results_file)

        except Exception as e:
            bot.send_message(message.chat.id, strings[user.lang].error_importing_data.format(error=str(e)))
            logger.error(f"Error importing data: {e}")
            data["state"].delete()