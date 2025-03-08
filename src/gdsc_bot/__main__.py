import os
import sys
from pathlib import Path
from typing import Final

from aiohttp import ClientSession
from discord import File, Game, Intents, Member
from discord.ext import commands
from dotenv import load_dotenv
from easy_pil import Editor, Font, load_image_async

# Loguru will enable us to log things, good for debugging
# Could have used default python logger also but this is easier to setup
# and I wanted to try it
from loguru import logger

# Load environment variables
# Stores private information soch as the `TOKEN` and the `GEMINI_API_KEY`
load_dotenv()
token = os.getenv("TOKEN")

if not token:
    logger.error("Unable to read token")
    sys.exit(1)

TOKEN: Final[str] = token
logger.debug("Token read successfully")


class Client(commands.Bot):
    def __init__(self) -> None:
        # If the user has a proxy, then use that for future networking operations
        proxy = os.getenv("http_proxy")
        self.proxy = proxy

        if proxy:
            logger.debug(f"Using proxy settings: {proxy}")

        # Intents lets us select what data we want discord to send to the bot
        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.guild_messages = True
        super().__init__(command_prefix=".", intents=intents, proxy=proxy)

    async def on_ready(self) -> None:
        """Hook activates when the bot has finished logging into discord and is ready"""
        # Set the rich presence thing, so it shows "Playing /help", so that the users can see the help command quickly
        await self.change_presence(activity=Game("/help"))

        # Set the `aiohttp` client to use our proxy settings
        self.client = ClientSession(proxy=self.proxy)
        logger.info(f"{self.user} is now running!")

    async def on_shutdown(self) -> None:
        logger.info("Goodbye!")
        # Remember to close the `aiohttp` client
        await self.client.close()

    async def setup_hook(self) -> None:
        """Load commands from the 'commands' folder during setup"""

        # Walk through every command file in the commands directory (python files) and load them as an extension.
        # So we don't have to manually import the commands
        current_file_path = Path(__file__).resolve()
        commands_dir = current_file_path.parent / "commands"

        for filename in commands_dir.iterdir():
            if filename.name.endswith(".py") and filename.name != "__init__.py":
                try:
                    await self.load_extension(f"gdsc_bot.commands.{filename.stem}")
                    logger.info(f"Loaded command: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load command {filename}: {e}")

        try:
            # Sync the slash commands with discord globally
            # BUG: This doesn't work always
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands globally")
        except Exception as e:
            logger.error(f"Error syncing commands: {e}")

    async def on_member_join(self, member: Member) -> None:
        """Send a welcome card to the user, use `easy_pil` to edit the background image"""
        if member.bot:
            return

        # Send the welcome message in the server's selected system channel
        channel = member.guild.system_channel
        if not channel:
            return
        logger.debug(f"New user joined: {member.id} on {member.guild.name}")

        background = Editor("assets/background.jpg")
        avatar_image = await load_image_async(member.display_avatar.url, self.client)

        avatar = Editor(avatar_image).resize((150, 150)).circle_image()
        poppins = Font.poppins(size=50, variant="bold")
        poppins_small = Font.poppins(size=20, variant="bold")
        background.paste(avatar, (325, 90))
        background.ellipse((325, 90), 150, 150, outline="white", stroke_width=5)

        background.text(
            (400, 260),
            f"Welcome to {member.guild.name}",
            color="white",
            font=poppins,
            align="center",
        )
        background.text(
            (400, 325),
            f"{member.name}",
            color="white",
            font=poppins_small,
            align="center",
        )

        file = File(fp=background.image_bytes, filename="welcome.jpg")

        await channel.send(
            f"Hello {member.mention}! Welcome To **{member.guild.name}**"
        )
        await channel.send(file=file)


def main() -> None:
    """Initialize and run the bot."""
    client = Client()
    client.run(TOKEN)


if __name__ == "__main__":
    main()
