import asyncio
import logging.config
import os

from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf
from telethon import TelegramClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/real_estate_telegram_bot/conf/config.yaml")
strings = config.strings

# Load environment variables
load_dotenv(find_dotenv(usecwd=True))
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
if API_ID is None:
    logger.error("Variable API_ID is not set")
if API_HASH is None:
    logger.error("Variable API_HASH is not set")


async def check_user_in_channel(channel_name: str, username: str):
    
    #PHONE = os.getenv("PHONE")


    # if PHONE is None:
    #     logger.error("Variable PHONE is not set")

    client = TelegramClient("user", API_ID, API_HASH)
    await client.start()
    logger.info(f"Checking users in channel {channel_name}")
    # get all the channels that I can access
    channels = {d.entity.username: d.entity
                for d in await client.get_dialogs()
                if d.is_channel}
    # choose the one that I want list users from
    channel = channels[channel_name]
    participants = await client.get_participants(channel)
    logger.info(f"Members of channel: {participants}")
    client.disconnect()
    return username in [member.username for member in participants]

def check_user_in_channel_sync(channel_name: str, username: str):
    return asyncio.run(check_user_in_channel(channel_name, username))

# To call the function from another file, you need to run it within an event loop
if __name__ == "__main__":
    channel_name = "happy_carrot_test"
    username = "konverner"
    result = check_user_in_channel_sync(channel_name, username)
