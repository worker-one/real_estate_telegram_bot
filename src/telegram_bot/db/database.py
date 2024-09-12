import datetime
import logging
import logging.config
import os

from dotenv import load_dotenv, find_dotenv
from omegaconf import OmegaConf
from requests import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .models import Base, Message, User

# Load logging configuration with OmegaConf
logging_config = OmegaConf.to_container(
    OmegaConf.load("./src/telegram_bot/conf/logging_config.yaml"),
    resolve=True
)
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(usecwd=True))

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    logger.error("DATABASE_URL is not set in the environment variables.")
    exit(1)

def get_enginge():
    return create_engine(
        DATABASE_URL,
        connect_args={'connect_timeout': 5, "application_name": "telegram_bot"},
        poolclass=NullPool
    )

def create_tables():
    engine = get_enginge()
    Base.metadata.create_all(engine)
    logger.info("Tables created")

def get_session():
    engine = get_enginge()
    return sessionmaker(bind=engine)()

def log_message(user_id, message_text):
    session = get_session()
    new_message = Message(
        timestamp=datetime.datetime.now(),
        user_id=user_id,
        message_text=message_text
    )
    session.add(new_message)
    session.commit()
    session.close()


def add_user(user_id, first_name, last_name, username, phone_number):
    session = get_session()
    new_user = User(
        user_id=user_id,
        first_message_timestamp=datetime.datetime.now(),
        first_name=first_name,
        last_name=last_name,
        username=username,
        phone_number=phone_number
    )
    # add only if the user is not already in the database
    if not session.query(User).filter(User.user_id == user_id).first():
        session.add(new_user)
    session.commit()
    session.close()
