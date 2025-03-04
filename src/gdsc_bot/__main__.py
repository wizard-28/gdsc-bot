import os
import sys
from typing import Final

import discord
from discord import Intents, Message
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger

from gdsc_bot.responses import get_response

# Load environment variables
load_dotenv()
token = os.getenv("TOKEN")

if not token:
    logger.error("Unable to read token")
    sys.exit(1)

TOKEN: Final[str] = token
logger.debug("Token read successfully")


class Client(commands.Bot):
    async def on_ready(self) -> None:
        logger.info(f"{self.user} is now running!")

        try:
            synced = await client.tree.sync()
            logger.info(f"Synced {len(synced)} commands globally")
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")

    async def on_message(self, message: Message) -> None:
        if message.author == self.user or message.author.bot:
            return

        logger.debug(f"[{message.channel}] {message.author}: {message.content}")
        await send_message(message, message.content)


async def send_message(message: Message, user_message: str) -> None:
    """Process user message and send a response."""
    if not user_message:
        logger.error("Message was empty, possibly due to missing intents.")
        return

    try:
        response = get_response(user_message)
        await message.channel.send(response)
    except Exception:
        logger.exception("Error while sending message")
        await message.channel.send("Oops! Something went wrong. Please try again.")


intents = Intents.default()
intents.message_content = True

proxy = os.getenv("PROXY")
client = Client(command_prefix=".", intents=intents, proxy=proxy)


@client.tree.command(name="hello", description="Say hello!")
async def say_hello(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Hello!")


def main() -> None:
    """Initialize and run the bot."""
    client.run(TOKEN)


if __name__ == "__main__":
    main()
