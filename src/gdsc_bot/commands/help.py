from datetime import datetime
import discord
from discord import Color, app_commands
from discord.ext import commands
from loguru import logger


class HelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Shows a list of available commands and their descriptions.",
    )
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            color=Color.dark_teal(),
            title="Bot Help Menu",
            description="Here are the available commands:",
            timestamp=datetime.now(),
        )

        # Iterate over all registered application commands
        for command in self.bot.tree.walk_commands():
            embed.add_field(
                name=f"/{command.name}",
                value=command.description or "No description",
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"User {interaction.user} used /help")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCommand(bot))
