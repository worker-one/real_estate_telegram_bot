import asyncio
import os

from dotenv import find_dotenv, load_dotenv
from telethon import TelegramClient


async def check_user_in_channel(channel_name: str, username: str):
    # Load environment variables
    load_dotenv(find_dotenv(usecwd=True))
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")

    client = TelegramClient('xxx', API_ID, API_HASH)
    await client.start()

    # get all the channels that I can access
    channels = {d.entity.username: d.entity
                for d in await client.get_dialogs()
                if d.is_channel}
    # choose the one that I want list users from
    channel = channels[channel_name]
    participants = await client.get_participants(channel)
    return username in [member.username for member in participants]

def check_user_in_channel_sync(channel_name: str, username: str):
    return asyncio.run(check_user_in_channel(channel_name, username))

# To call the function from another file, you need to run it within an event loop
if __name__ == "__main__":
    channel_name = "happy_carrot_test"
    username = "konverner"
    result = check_user_in_channel_sync(channel_name, username)
    print(result)
