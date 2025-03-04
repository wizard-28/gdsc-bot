import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class HelloCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hello", description="Say hello!")
    async def say_hello(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message("Hello!")
        logger.info(f"User {interaction.user} used /hello")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelloCommand(bot))
