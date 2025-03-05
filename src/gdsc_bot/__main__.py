import os
import sys
from typing import Final

from pathlib import Path
from aiohttp import ClientSession
from discord import File, Intents, Member, Message, Game
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger
from easy_pil import Editor, Font, load_image_async

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
        proxy = os.getenv("http_proxy")
        self.proxy = proxy

        if proxy:
            logger.debug(f"Using proxy settings: {proxy}")

        intents = Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.guild_messages = True
        super().__init__(command_prefix=".", intents=intents, proxy=proxy)

    async def on_ready(self) -> None:
        await self.change_presence(activity=Game("/help"))
        self.client = ClientSession(proxy=self.proxy)
        logger.info(f"{self.user} is now running!")

    async def on_shutdown(self) -> None:
        logger.info("Goodbye!")
        await self.client.close()

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

    async def on_member_join(self, member: Member) -> None:
        if member.bot:
            return

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
