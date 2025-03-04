import os
import sys
from typing import Final

from pathlib import Path
from discord import Intents, Message
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()
token = os.getenv("TOKEN")

if not token:
    logger.error("Unable to read token")
    sys.exit(1)

TOKEN: Final[str] = token
logger.debug("Token read successfully")


class Client(commands.Bot):
    def __init__(self) -> None:
        proxy = os.getenv("PROXY")

        if proxy:
            logger.debug(f"Using proxy settings: {proxy}")

        super().__init__(command_prefix=".", intents=Intents.default(), proxy=proxy)
        self.intents.message_content = True

    async def on_ready(self) -> None:
        logger.info(f"{self.user} is now running!")

    async def setup_hook(self) -> None:
        """Load commands from the 'commands' folder"""

        current_file_path = Path(__file__).resolve()
        commands_dir = current_file_path.parent / "commands"

        for filename in commands_dir.iterdir():
            if filename.name.endswith(".py") and filename.name != "__init__.py":
                try:
                    await self.load_extension(f"gdsc_bot.commands.{filename.name[:-3]}")
                    logger.info(f"Loaded command: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load command {filename}: {e}")

        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands globally")
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")

    async def on_message(self, message: Message) -> None:
        if message.author == self.user or message.author.bot:
            return

        logger.debug(f"[{message.channel}] {message.author}: {message.content}")


def main() -> None:
    """Initialize and run the bot."""
    client = Client()
    client.run(TOKEN)


if __name__ == "__main__":
    main()
