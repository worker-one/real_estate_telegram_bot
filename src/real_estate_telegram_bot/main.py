from real_estate_telegram_bot.api.bot import start_bot
from real_estate_telegram_bot.db.database import create_tables

if __name__ == "__main__":
    create_tables()
    start_bot()
