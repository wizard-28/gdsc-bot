from typing import Optional
import discord
from discord.ext import commands
from discord import app_commands
from loguru import logger

from gdsc_bot import GDSCEmbed


class PollCommand(commands.Cog):
    """
    Allows the user to set polls.

    They can specify a maximum of 10 choices, 2 being compulsory.

    The author can end the poll by reacting with the tick mark emoji.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Create a poll! (max 10 choices)")
    @app_commands.describe(
        title="Enter your message",
        choice1="Choice 1",
        choice2="Choice 2",
        choice3="Choice 3 (optional)",
        choice4="Choice 4 (optional)",
        choice5="Choice 5 (optional)",
        choice6="Choice 6 (optional)",
        choice7="Choice 7 (optional)",
        choice8="Choice 8 (optional)",
        choice9="Choice 9 (optional)",
        choice10="Choice 10 (optional)",
    )
    async def poll(
        self,
        interaction: discord.Interaction,
        title: str,
        choice1: str,
        choice2: str,
        choice3: Optional[str],
        choice4: Optional[str],
        choice5: Optional[str],
        choice6: Optional[str],
        choice7: Optional[str],
        choice8: Optional[str],
        choice9: Optional[str],
        choice10: Optional[str],
    ) -> None:
        logger.info(f"User {interaction.user} used /poll")

        # Keep all the choices in a list, for easier manipulation
        choices = [
            choice1,
            choice2,
            choice3,
            choice4,
            choice5,
            choice6,
            choice7,
            choice8,
            choice9,
            choice10,
        ]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        valid_choices = [choice for choice in choices if choice]

        # Prepare the poll embed
        description = "\n".join(
            [f"{emojis[i]} {choice}" for i, choice in enumerate(valid_choices)]
        )

        # Send the inital poll message with the polls
        poll_embed = GDSCEmbed(title=title, description=description).set_footer(
            text=f"Poll by {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url,
        )
        await interaction.response.send_message(embed=poll_embed)

        # Fetch the sent message to add the reaction buttons
        fetched_msg = await interaction.original_response()

        # Add reaction buttons
        for i in range(len(valid_choices)):
            await fetched_msg.add_reaction(emojis[i])

        await fetched_msg.add_reaction("✅")

        # Used for the percentage calculation later
        total_reactions = 0

        def check_if_the_author_reacted_with_tick(
            reaction: discord.Reaction, user: discord.Member
        ) -> bool:
            nonlocal total_reactions
            if reaction.message.id != fetched_msg.id:
                return False

            if str(reaction.emoji) in emojis:
                total_reactions += 1

            return str(reaction.emoji) == "✅" and user == interaction.user

        await self.bot.wait_for(
            "reaction_add", check=check_if_the_author_reacted_with_tick
        )

        # Fetch updated message to get reaction counts
        channel = interaction.channel
        assert channel
        fetched_msg = await channel.fetch_message(fetched_msg.id)

        # Subtract one as we don't want to count the bot's own reaction.
        counts = [
            (valid_choices[i], reaction.count - 1)
            for i, reaction in enumerate(fetched_msg.reactions)
            if reaction.emoji in emojis
        ]

        result = "\n".join(
            [
                f"{choice}: {count / total_reactions * 100:.2f}% ({count} votes)"
                for choice, count in counts
            ]
        )

        result_embed = GDSCEmbed(
            title="Poll results",
            url=fetched_msg.jump_url,
            description=result,
        ).set_footer(
            text=f"Poll by {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.followup.send(embed=result_embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PollCommand(bot))
