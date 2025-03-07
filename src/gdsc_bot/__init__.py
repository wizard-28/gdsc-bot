from datetime import datetime
from typing import Any, Optional, Union

import discord
from discord import Color
from discord.types.embed import EmbedType


class GDSCEmbed(discord.Embed):
    """Subclass `discord.Embed` so we don't have to repeat the same parameters again and again"""

    def __init__(
        self,
        bot: discord.Client,
        *,
        color: Optional[Union[int, Color]] = Color.dark_teal(),
        title: Optional[Any] = None,
        type: EmbedType = "rich",
        url: Optional[Any] = None,
        description: Optional[Any] = None,
        timestamp: Optional[datetime] = None,
    ):
        if timestamp is None:
            timestamp = datetime.now()
        super().__init__(
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        assert bot.user
        self.set_thumbnail(url=bot.user.display_avatar.url)
        self.set_author(
            name=bot.user.display_name, icon_url=bot.user.display_avatar.url
        )


class SuccessEmbed(discord.Embed):
    def __init__(
        self,
        bot: discord.Client,
        *,
        color: Optional[Union[int, Color]] = Color.green(),
        title: Optional[Any] = "Success",
        type: EmbedType = "rich",
        url: Optional[Any] = None,
        description: Optional[Any] = None,
        timestamp: Optional[datetime] = None,
    ):
        if timestamp is None:
            timestamp = datetime.now()
        super().__init__(
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        assert bot.user
        self.set_thumbnail(
            url="https://em-content.zobj.net/source/twitter/408/check-mark-button_2705.png"
        )
        self.set_author(
            name=bot.user.display_name, icon_url=bot.user.display_avatar.url
        )


class ErrorEmbed(discord.Embed):
    def __init__(
        self,
        bot: discord.Client,
        *,
        color: Optional[Union[int, Color]] = Color.red(),
        title: Optional[Any] = "Error",
        type: EmbedType = "rich",
        url: Optional[Any] = None,
        description: Optional[Any] = None,
        timestamp: Optional[datetime] = None,
    ):
        if timestamp is None:
            timestamp = datetime.now()
        super().__init__(
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
        assert bot.user
        self.set_thumbnail(
            url="https://em-content.zobj.net/source/twitter/408/cross-mark_274c.png"
        )
        self.set_author(
            name=bot.user.display_name, icon_url=bot.user.display_avatar.url
        )
