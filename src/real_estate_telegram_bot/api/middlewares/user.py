import logging

from telebot.handler_backends import BaseMiddleware
from telebot.types import CallbackQuery, Message

from real_estate_telegram_bot.db import crud

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserMessageMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.update_types = ["message"]

    def pre_process(self, message: Message, data: dict):
        user = crud.upsert_user(
            id=message.from_user.id,
            username=message.from_user.username
        )
        event = crud.create_event(user_id=user.id, content=message.text, type="message")
        # Log event to the console
        logger.info(event.dict())

        # Set the user data to the data dictionary
        data["user"] = user

    def post_process(self, message, data, exception):
        pass


class UserCallbackMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.update_types = ["callback_query"]

    def pre_process(self, callback_query: CallbackQuery, data: dict):
        user = crud.upsert_user(
            id=callback_query.from_user.id,
            username=callback_query.from_user.username
        )
        event = crud.create_event(user_id=user.id, content=callback_query.data, type="callback")

        # Log event to the console
        logger.info(event.dict())

        # Set the user data to the data dictionary
        data["user"] = user

    def post_process(self, callback_query, data, exception):
        pass
