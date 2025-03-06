import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from gdsc_bot import GDSCEmbed


class HelpCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Shows a list of available commands and their descriptions.",
    )
    async def help(self, interaction: discord.Interaction) -> None:
        assert self.bot.user
        embed = GDSCEmbed(
            self.bot,
            title="Bot Help Menu",
            description="Here are the available commands:",
        )

        # Organize commands by group
        command_groups: dict[str, list[str]] = {}
        for command in self.bot.tree.walk_commands():
            group_name = command.parent.name.title() if command.parent else "General"
            if group_name not in command_groups:
                command_groups[group_name] = []

            if isinstance(command, app_commands.Command):
                params = " ".join(
                    [f"`[{param.display_name}]`" for param in command.parameters]
                )
                command_groups[group_name].append(
                    f"**/{command.qualified_name}** {params}\n{command.description}"
                )

        # Add each group to the embed
        for group, commands_list in command_groups.items():
            embed.add_field(name=group, value="\n".join(commands_list))

        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"User {interaction.user} used /help")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCommand(bot))
