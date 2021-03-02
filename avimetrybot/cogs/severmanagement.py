from discord.ext import commands
from typing import Optional
import discord


class ServerManagement(commands.Cog):

    async def deep_clone_category(category: discord.CategoryChannel, name: Optional[str] = None):
        cloned = await category.clone(name=name)

        for channel in category.channels:
            cloned_channel = await channel.clone()
            await cloned_channel.edit(category=cloned)
        return cloned
