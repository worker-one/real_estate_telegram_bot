import logging

from fastapi import APIRouter
from telebot import TeleBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_router(bot: TeleBot) -> APIRouter:
    """ Create the health check router """
    router = APIRouter()

    logger.info("Creating the health check router")
    @router.get("/health")
    def health_check() -> bool:
        return True

    return router
