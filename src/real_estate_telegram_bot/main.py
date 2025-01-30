import os
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """Initialize the database."""
    from real_estate_telegram_bot.db import crud
    from real_estate_telegram_bot.db.database import create_tables
    # Create tables
    create_tables()

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

    # Add admin to user table
    if ADMIN_USERNAME:
        user = crud.upsert_user(id=ADMIN_USER_ID, username=ADMIN_USERNAME, role="admin", lang="en")
        logger.info(f"User '{user.username}' ({user.id}) added to the database with admin role.")

    logger.info("Database initialized")


if __name__ == "__main__":
    # Load and get environment variables
    from dotenv import find_dotenv, load_dotenv
    load_dotenv(find_dotenv(usecwd=True, raise_error_if_not_found=True), override=True)

    # Initialize the database
    init_db()

    from real_estate_telegram_bot.api.bot import start_bot
    start_bot()
