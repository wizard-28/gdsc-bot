import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, cast

import discord
from discord import Member, User, app_commands
from discord.ext import commands
from loguru import logger
from rapidfuzz import process
from sortedcontainers import SortedList, SortedSet

from gdsc_bot import ErrorEmbed, GDSCEmbed, SuccessEmbed


class PastDateTimeError(Exception):
    """The date passed in was already over."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


@dataclass(order=True)
class Reminder:
    dt: datetime
    message: str


DATE_TIME_FORMAT = (
    "%B %d, %I:%M %p"  # <month> <date>, <12-hours hour>:<minutes> <AM/PM>
)
DATE_FORMAT = "%d-%m-%Y"  # <date>-<month>-<year>
TIME_FORMAT = "%I:%M %p"  # <12-hours hour>:<minutes> <AM/PM>
CHECKING_FREQUENCY = 3


class ReminderManager:
    def __init__(self) -> None:
        self.reminders: defaultdict[User | Member, SortedList] = defaultdict(
            lambda: SortedList()
        )

    def list_reminders(self, user: User | Member) -> SortedSet | None:
        return self.reminders.get(user)

    def set_reminder(self, user: User | Member, dt: datetime, message: str) -> None:
        reminder = Reminder(dt, message)

        if reminder in self.reminders[user]:
            raise ValueError("The reminder already exists")

        self.reminders[user].add(Reminder(dt, message))

    def modify_reminder(
        self,
        user: User | Member,
        old_reminder: Reminder,
        dt: datetime | None = None,
        message: str | None = None,
    ) -> None:
        """
        Raises ValueError
        """
        if not message and not dt:
            raise ValueError("At least datetime or message should be present")
        message = message if message else old_reminder.message
        dt = dt if dt else old_reminder.dt

        new_reminder = Reminder(dt, message)

        if new_reminder in self.reminders[user]:
            raise ValueError(
                "You can't edit a reminder to make it the same as another reminder"
            )

        self.reminders[user].remove(old_reminder)
        self.reminders[user].add(Reminder(dt, message))

    def delete_reminder(self, user: User | Member, reminder: Reminder) -> None:
        self.reminders[user].remove(reminder)

        if not self.reminders[user]:
            del self.reminders[user]

    def get_expired_reminders(self) -> list[tuple[User | Member, Reminder]]:
        expired_reminders = []
        for user, reminders in self.reminders.items():
            for reminder in reminders:
                if reminder.dt < datetime.now():
                    expired_reminders.append((user, reminder))
                else:
                    # Since the reminders are sorted, we can break as soon as we don't find a expired reminder
                    break

        logger.debug(f"{expired_reminders = }")
        return expired_reminders

    def get_reminder(self, user: User | Member, reminder_index: int) -> Reminder:
        return cast(Reminder, self.reminders[user][reminder_index])


class RemindCommand(commands.GroupCog, group_name="reminders"):  # type: ignore[call-arg]
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Min-heap, the earliest reminder is at index 0
        self.reminder_manager = ReminderManager()

        # Create a background task to check the reminders
        self.bot.loop.create_task(self.check_reminders())

    async def check_reminders(self) -> None:
        """Check the first element in the `self.reminders` min-heap, if it's expired every 3 seconds."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            logger.debug("Checking reminders...")

            for user, reminder in self.reminder_manager.get_expired_reminders():
                if not (channel := user.dm_channel):
                    channel = await user.create_dm()

                embed = GDSCEmbed(
                    self.bot,
                    description=f"On <t:{int(reminder.dt.timestamp())}> you asked me to remind you about: {reminder.message}",
                )
                if isinstance(user, Member):
                    if user.guild.icon:
                        embed.set_thumbnail(url=user.guild.icon.url)
                await channel.send(embed=embed)

                self.reminder_manager.delete_reminder(user, reminder)

            await asyncio.sleep(CHECKING_FREQUENCY)

    async def reminder_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[int]]:
        """
        Provides auto completion for reminder slash command

        If no `current` input is present then show all the reminders with their timestamp.
        Otherwise use `rapidfuzz` to fuzzy search the top 5 best reminder matches accoring to the reminder message
        and show that.

        Returns the reminder
        """
        reminders = self.reminder_manager.list_reminders(interaction.user)
        if not reminders:
            return []
        if not current:  # If no input, return all options
            return [
                app_commands.Choice(
                    name=f"{reminder.message} at {reminder.dt.strftime(DATE_TIME_FORMAT)}",
                    value=i,
                )
                # Show all the reminders from the earliest to the latest
                for i, reminder in enumerate(reminders)
            ]

        # Create a dictionary mapping messages to their index
        message_index_map = {
            f"{reminder.message}: {reminder.dt.strftime(DATE_TIME_FORMAT)}": reminder
            for reminder in reminders
        }

        # Perform fuzzy matching
        matches = process.extract(current, message_index_map.keys(), limit=5)

        return [
            app_commands.Choice(
                name=f"{match} at {message_index_map[match].dt.strftime(DATE_TIME_FORMAT)}",
                value=reminders.index(message_index_map[match]),
            )
            for (match, _, _) in matches
        ]

    def calculate_datetime(self, time: str, day: Optional[str] = None) -> datetime:
        dt = datetime.strptime(time, TIME_FORMAT)
        now = datetime.now()

        if day:
            dt = datetime.combine(datetime.strptime(day, DATE_FORMAT), dt.time())
        else:
            dt = datetime.combine(now.date(), dt.time())

            # If the time has already passed today, set it for tomorrow
            if dt < now:
                dt += timedelta(days=1)

        # If the user specifies a past date, inform them
        if dt < now:
            if dt.date() < now.date():
                raise PastDateTimeError(message="The day passed in is already over")
            if dt.time() < now.time():
                raise PastDateTimeError(message="The time passed in is already over")

        logger.debug(f"Calculated date time: {dt}")
        return dt

    @app_commands.command(
        name="modify",
        description="Modify a reminder! At least any one of `message`, `time` or `day` needs to be edited",
    )
    @app_commands.describe(
        message="the reminder message",
        old_reminder="the reminder you want to edit",
        time=f"set the time in  {TIME_FORMAT} (Ex: 12:30 PM)",
        day=f"set the date in {DATE_FORMAT} (Ex: 12-12-2025)",
    )
    @app_commands.autocomplete(old_reminder=reminder_autocomplete)
    async def modify_reminder(
        self,
        interaction: discord.Interaction,
        old_reminder: int,
        message: Optional[str],
        time: Optional[str],
        day: Optional[str],
    ) -> None:
        """
        This command lets the user modify an already existing reminder.

        The user has to filter the reminder by entering some part of the reminder message which is then fuzzy searched in `reminder_autocomplete` to match the actual reminder.

        Then the future time is calculated, the old reminder is deleted and the new reminder is added.
        """
        old_reminder_val = self.reminder_manager.get_reminder(
            interaction.user, old_reminder
        )

        if not message and not time and not day:
            error_embed = ErrorEmbed(
                self.bot, description="Reminder unmodified, it stays the same"
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

        if message and not time and not day:
            try:
                self.reminder_manager.modify_reminder(
                    interaction.user, old_reminder_val, message=message
                )
            except ValueError as e:
                error_embed = ErrorEmbed(self.bot, description=f"{e}")
                await interaction.response.send_message(
                    embed=error_embed, ephemeral=True
                )
                return

            await interaction.response.send_message(
                embed=SuccessEmbed(self.bot, description="Reminder message changed!"),
                ephemeral=True,
            )
            return

        if not message and not (time or day):
            await interaction.response.send_message(
                embed=ErrorEmbed(
                    self.bot,
                    description="You have to specify either the time or the day or the message",
                )
            )
            return

        logger.info(f"User {interaction.user} used /modifyreminder")

        try:
            if time:
                dt = self.calculate_datetime(time, day)
            else:
                dt = self.calculate_datetime(
                    time=old_reminder_val.dt.time().strftime(TIME_FORMAT), day=day
                )

            try:
                self.reminder_manager.modify_reminder(
                    interaction.user, old_reminder_val, dt, message
                )
                await interaction.response.send_message(
                    embed=SuccessEmbed(
                        self.bot, description="Reminder modified successfully!"
                    )
                )
            except ValueError as e:
                await interaction.response.send_message(
                    embed=ErrorEmbed(self.bot, description=f"{e}"), ephemeral=True
                )
                return
        except (ValueError, PastDateTimeError) as e:
            await interaction.response.send_message(
                embed=ErrorEmbed(self.bot, description=f"Invalid time: {e}"),
                ephemeral=True,
            )
            logger.error(f"{e}")

    @app_commands.command(name="delete", description="Delete a reminder!")
    @app_commands.describe(
        reminder="the reminder you want to edit",
    )
    @app_commands.autocomplete(reminder=reminder_autocomplete)
    async def delete_reminder(
        self, interaction: discord.Interaction, reminder: int
    ) -> None:
        """Allows the user to delete a old reminder"""
        logger.info(f"User {interaction.user} used /deletereminder")
        self.reminder_manager.delete_reminder(
            interaction.user,
            self.reminder_manager.get_reminder(interaction.user, reminder),
        )

        await interaction.response.send_message(
            embed=SuccessEmbed(self.bot, description="Reminder deleted successfully!"),
            ephemeral=True,
        )

    @app_commands.command(name="set", description="Set a reminder!")
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
            self.reminder_manager.set_reminder(interaction.user, dt, message)
            await interaction.response.send_message(
                embed=SuccessEmbed(
                    self.bot,
                    description=f"I'll remind you on <t:{int(dt.timestamp())}>",
                )
            )
        except PastDateTimeError as e:
            await interaction.response.send_message(
                embed=ErrorEmbed(self.bot, description=f"Invalid time: {e}"),
                ephemeral=True,
            )
            logger.error(f"{e}")
        except ValueError as e:
            await interaction.response.send_message(
                embed=ErrorEmbed(self.bot, description=f"{e}")
            )

    @app_commands.command(name="list", description="List all reminders!")
    async def list_reminder(self, interaction: discord.Interaction) -> None:
        """Allows the user to list existing reminders"""
        logger.info(f"User {interaction.user} used /listreminders")

        reminders = self.reminder_manager.list_reminders(interaction.user)
        if not reminders:
            embed = GDSCEmbed(
                self.bot,
                title="Reminders",
                description="No reminders set. Set reminders using `/reminders set` command!",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        reminders_str = "\n".join(
            f"{i}. <t:{int(reminder.dt.timestamp())}>: {reminder.message}"
            for i, reminder in enumerate(reminders, start=1)
        )

        embed = GDSCEmbed(self.bot, title="Reminders", description=reminders_str)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RemindCommand(bot))
