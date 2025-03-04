from typing import Optional, Union, Any
import discord
from discord import Color
from discord.types.embed import EmbedType
from datetime import datetime


# Subclass `discord.Embed` so we don't have to repeat the same parameters again and again
class GDSCEmbed(discord.Embed):
    def __init__(
        self,
        *,
        color: Optional[Union[int, Color]] = Color.dark_teal(),
        title: Optional[Any] = None,
        type: EmbedType = "rich",
        url: Optional[Any] = None,
        description: Optional[Any] = None,
        timestamp: Optional[datetime] = datetime.now(),
    ):
        super().__init__(
            color=color,
            title=title,
            type=type,
            url=url,
            description=description,
            timestamp=timestamp,
        )
