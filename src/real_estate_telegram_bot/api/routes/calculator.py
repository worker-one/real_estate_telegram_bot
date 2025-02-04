import logging
from typing import Optional
import os

from fastapi import APIRouter
from omegaconf import OmegaConf
from telebot import TeleBot

from real_estate_telegram_bot.api.middlewares import user
from real_estate_telegram_bot.core.excel import format_calculator_result, to_pdf

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/apps/calculator.yaml")
strings = config.strings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from datetime import date

from pydantic import BaseModel
from telebot.util import parse_web_app_data
from telebot.util import validate_web_app_data


class RealEstateTransaction(BaseModel):
    projectName: str
    calculationDate: str
    salePrice: float
    paymentSeller: float
    paymentTransfer: float
    dldFee: float
    constructionFee: float
    registrationTrusteeFee: float
    agentCommission: float
    mortgagePaymentsAmounts: list[float]
    mortgagePaymentsPercents: Optional[list[float]] = None
    mortgagePaymentsDates: Optional[list[str]] = None
    sellerCheque: bool
    dldCheque: bool
    commissionCheque: Optional[bool] = None
    managersChequeAmount: Optional[float] = None
    managersChequePercent: Optional[float] = None
    paymentPlan: Optional[float] = None
    totalPrice: float
    initData: str
    user_id: int


def create_router(bot: TeleBot) -> APIRouter:
    """ Create the calculator router """
    router = APIRouter()

    logger.info("Creating calculator router")

    @router.post("/download/pdf")
    def download_pdf(data: RealEstateTransaction):

        initData = data.initData
        print(data)
        if validate_web_app_data(bot.token, initData):
            web_app_data = parse_web_app_data(bot.token, initData)

            user_id = web_app_data['user']['id']
            # user_id = data.user_id
            user_dir = f"data/{user_id}"

            # Download file as a excel
            if not os.path.exists(user_dir):
                os.makedirs(user_dir, exist_ok=True)

            filename = data.projectName.replace(" ", "_")
            filepath = f"{user_dir}/{filename}.xlsx"
            format_calculator_result(data, filepath)

            # Convert the excel file to pdf
            filepath = to_pdf(filepath)

            with open(filepath, "rb") as file:
                bot.send_document(user_id, file)

            return {"filepath": filepath}

    @router.post("/download/excel")
    def download_excel(data: RealEstateTransaction):
        initData = data.initData
        if validate_web_app_data(bot.token, initData):
            web_app_data = parse_web_app_data(bot.token, initData)

            user_id = web_app_data['user']['id']
            user_dir = f"data/{user_id}"

            if not os.path.exists(user_dir):
                os.makedirs(user_dir, exist_ok=True)

            filename = data.projectName.replace(" ", "_")
            filepath = f"{user_dir}/{filename}.xlsx"

            format_calculator_result(data, filepath)

            # Send the file to the user
            with open(filepath, "rb") as file:
                bot.send_document(user_id, file)
            return {"filepath": filepath}

    return router
