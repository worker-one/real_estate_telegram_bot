import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from omegaconf import OmegaConf
from pydantic import BaseModel
from telebot import TeleBot
from telebot.util import parse_web_app_data, validate_web_app_data

from real_estate_telegram_bot.core.excel import format_calculator_result, to_pdf

# Load configuration
config = OmegaConf.load("./src/real_estate_telegram_bot/conf/apps/calculator.yaml")
strings = config.strings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def create_router(bot: TeleBot) -> APIRouter:
    """Create and configure the calculator router"""
    router = APIRouter()
    logger.info("Creating calculator router")

    def process_request(data: RealEstateTransaction, file_format: str) -> None:
        """Process the request and send the appropriate file format"""
        # Validate web app data
        if not validate_web_app_data(bot.token, data.initData):
            logger.warning("Invalid initData received")
            raise HTTPException(status_code=401, detail="Unauthorized")

        try:
            web_app_data = parse_web_app_data(bot.token, data.initData)
        except Exception as e:
            logger.error("Error parsing web app data: %s", e)
            raise HTTPException(status_code=400, detail="Invalid initData format")

        user_id = web_app_data["user"]["id"]
        user_dir = f"data/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        excel_path = f"{user_dir}/calculator.xlsx"
        pdf_path = None

        try:
            # Generate Excel file
            format_calculator_result(data, excel_path)

            if file_format == "pdf":
                # Convert to PDF and clean up Excel
                pdf_path = to_pdf(excel_path)
                os.remove(excel_path)
                file_to_send = pdf_path
            else:
                file_to_send = excel_path

            # Send the file
            with open(file_to_send, "rb") as file:
                bot.send_document(user_id, file)

        except Exception as e:
            logger.error("Error processing/sending file: %s", e)
            raise HTTPException(status_code=500, detail="File processing failed")
        finally:
            # Clean up temporary files
            if file_format == "pdf" and pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
            elif file_format == "excel" and os.path.exists(excel_path):
                os.remove(excel_path)

    @router.post("/download/pdf")
    def download_pdf_endpoint(data: RealEstateTransaction):
        """Endpoint to generate and send PDF report"""
        process_request(data, "pdf")
        return {"status": "PDF sent successfully"}

    @router.post("/download/excel")
    def download_excel_endpoint(data: RealEstateTransaction):
        """Endpoint to generate and send Excel report"""
        process_request(data, "excel")
        return {"status": "Excel sent successfully"}

    return router
