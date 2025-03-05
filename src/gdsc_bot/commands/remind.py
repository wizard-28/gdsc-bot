import asyncio
import discord
from discord import User, app_commands, Member
from discord.ext import commands
from loguru import logger
from datetime import datetime, timedelta
from typing import NamedTuple, Optional
from rapidfuzz import process, fuzz

from gdsc_bot import GDSCEmbed


class PastDateError(Exception):
    """The date passed in was already over."""

    def __init__(self, message: str = "The day passed in is already over!") -> None:
        self.message = message
        super().__init__(self.message)


class Reminder(NamedTuple):
    """
    NamedTuple subclass used to keep track of reminders.

    Used this instead of just a regular tuple, as this allows using the `.` (dot) operator to access the elements
    """

    user: User | Member
    message: str
    dt: datetime


DATE_TIME_FORMAT = (
    "%B %d, %I:%M %p"  # <month> <date>, <12-hours hour>:<minutes> <AM/PM>
)
DATE_FORMAT = "%d-%m-%Y"  # <date>-<month>-<year>
TIME_FORMAT = "%I:%M %p"  # <12-hours hour>:<minutes> <AM/PM>


class RemindCommand(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.reminders: list[Reminder] = []
        # Create a background task to check the reminders
        self.bot.loop.create_task(self.check_reminders())

    async def check_reminders(self) -> None:
        """Loops through every reminder in `self.reminders` to check if they're expired. If so then DM the user and delete the task.

        Repeat this every 3 seconds
        """
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            logger.debug(f"Checking {len(self.reminders)} reminders...")
            for i, reminder in enumerate(self.reminders):
                # Check if less than 3 seconds are left, if so then DM the user
                if (reminder.dt - reminder.dt.now()).total_seconds() <= 3:
                    if not (channel := reminder.user.dm_channel):
                        channel = await reminder.user.create_dm()

                    await channel.send(content=reminder.message)
                    del self.reminders[i]

            # Repeat this every 3 seconds
            await asyncio.sleep(3)

    async def reminder_autocomplete(
        self, _interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[int]]:
        """
        Provides auto completion for reminder slash command

        If no `current` input is present then show all the reminders with their timestamp.
        Otherwise use `rapidfuzz` to fuzzy search the top 5 best reminder matches accoring to the reminder message
        and show that.

        Returns the index of the selected reminder.
        """
        if not current:  # If no input, return all options
            return [
                app_commands.Choice(
                    name=f"{msg} at {dt.strftime(DATE_TIME_FORMAT)}", value=i
                )
                for i, (_, msg, dt) in enumerate(self.reminders)
            ]

        # Create a dictionary mapping messages to their index
        message_index_map = {
            msg: (i, dt) for i, (_, msg, dt) in enumerate(self.reminders)
        }

        # Perform fuzzy matching
        matches = process.extract(
            current, message_index_map.keys(), limit=5, scorer=fuzz.ratio
        )

        return [
            app_commands.Choice(
                name=f"{match} at {message_index_map[match][1].strftime(DATE_TIME_FORMAT)}",
                value=message_index_map[match][0],
            )
            for (match, _, _) in matches
        ]

    def calculate_datetime(self, time: str, day: Optional[str]) -> datetime:
        dt = datetime.strptime(time, TIME_FORMAT)
        now = datetime.now()

        if day:
            dt = datetime.combine(datetime.strptime(day, DATE_FORMAT), dt.time())
            # If the user specifies a past date, inform them
            if dt < now:
                raise PastDateError()
        else:
            dt = datetime.combine(now.date(), dt.time())

            # If the time has already passed today, set it for tomorrow
            if dt < now:
                dt += timedelta(days=1)

        logger.debug(f"Calculated date time: {dt}")
        return dt

    @app_commands.command(name="modifyreminder", description="Modify a reminder!")
    @app_commands.describe(
        message="the reminder message",
        reminder="the reminder you want to edit",
        time=f"set the time in  {TIME_FORMAT} (Ex: 12:30 PM)",
        day=f"set the date in {DATE_FORMAT} (Ex: 12-12-2025)",
    )
    @app_commands.autocomplete(reminder=reminder_autocomplete)
    async def modify_reminder(
        self,
        interaction: discord.Interaction,
        reminder: int,
        message: Optional[str],
        time: str,
        day: Optional[str],
    ) -> None:
        """
        This command lets the user modify an already existing reminder.

        The user has to filter the reminder by entering some part of the reminder message which is then fuzzy searched in `reminder_autocomplete` to match the actual reminder.

        Then the future time is calculated, the old reminder is deleted and the new reminder is added.
        """
        logger.info(f"User {interaction.user} used /modifyreminder")
        # If the user didn't specify a `message` then reuse the old `message`
        msg = message if message else self.reminders[reminder][1]

        try:
            dt = self.calculate_datetime(time, day)
            await interaction.response.send_message(
                f"I'll remind you on <t:{int(dt.timestamp())}>"
            )
            del self.reminders[reminder]
            self.reminders.append(Reminder(interaction.user, msg, dt))
        except ValueError as e:
            await interaction.response.send_message(
                f"Invalid time: {e}", ephemeral=True
            )
            logger.error(f"Invalid time: {e}")
        except PastDateError as e:
            await interaction.response.send_message(e, ephemeral=True)
            logger.error(f"{e}")

    @app_commands.command(name="setreminder", description="Set a reminder!")
    @app_commands.describe(
        message="the reminder message",
        time=f"set the time in {TIME_FORMAT} (Ex: 12:30 PM)",
        day=f"set the date in {DATE_FORMAT} (Ex: 12-12-2025)",
    )
    async def set_reminder(
        self,
        interaction: discord.Interaction,
        message: str,
        time: str,
        day: Optional[str],
    ) -> None:
        """Allows the user to set a new reminder"""
        logger.info(f"User {interaction.user} used /setreminder")
        try:
            dt = self.calculate_datetime(time, day)
            if (
                reminder := Reminder(interaction.user, message, dt)
            ) not in self.reminders:
                await interaction.response.send_message(
                    f"I'll remind you on <t:{int(dt.timestamp())}>"
                )
                self.reminders.append(reminder)
            else:
                await interaction.response.send_message(
                    "The reminder already exists!", ephemeral=True
                )
        except ValueError as e:
            await interaction.response.send_message(
                f"Invalid time: {e}", ephemeral=True
            )
            logger.error(f"Invalid time: {e}")
        except PastDateError as e:
            await interaction.response.send_message(f"{e}", ephemeral=True)
            logger.error(f"{e}")

    @app_commands.command(name="listreminders", description="List all reminders!")
    async def list_reminder(self, interaction: discord.Interaction) -> None:
        """Allows the user to list existing reminders"""
        logger.info(f"User {interaction.user} used /listreminders")
        reminders = [
            f"{i}. <t:{int(dt.timestamp())}>: {msg}"
            for i, (_, msg, dt) in enumerate(self.reminders)
        ]
        desp = "\n".join(reminders)

        embed = GDSCEmbed(
            title="Reminders",
            description=desp
            if reminders
            else "No reminders set. Set reminders using `/setreminder` command!",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RemindCommand(bot))
