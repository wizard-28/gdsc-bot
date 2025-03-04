import os
import sys
from typing import Final

from discord import Client, Intents, Message
from dotenv import load_dotenv
from loguru import logger

from gdsc_bot.responses import get_response

# Load environment variables
load_dotenv()
token = os.getenv("TOKEN")

if not token:
    logger.error("Unable to read token")
    sys.exit(-1)

TOKEN: Final[str] = token
logger.debug("Token read successfully")


async def send_message(message: Message, user_message: str) -> None:
    """Process user message and send a response."""
    if not user_message:
        logger.error("Message was empty because intents were not enabled probably")
        return

    try:
        response = get_response(user_message)
        await message.channel.send(response)
    except Exception:
        logger.exception("Error while sending message")
        await message.channel.send("Oops! Something went wrong. Please try again.")


def main() -> None:
    """Initialize and run the bot."""
    intents = Intents.default()
    intents.message_content = True

    proxy = os.getenv("PROXY")
    client = Client(intents=intents, proxy=proxy) if proxy else Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        logger.info(f"{client.user} is now running!")

    @client.event
    async def on_message(message: Message) -> None:
        if message.author == client.user or message.author.bot:
            return

        logger.debug(f"[{message.channel}] {message.author}: {message.content}")
        await send_message(message, message.content)

    client.run(TOKEN)


if __name__ == "__main__":
    main()
