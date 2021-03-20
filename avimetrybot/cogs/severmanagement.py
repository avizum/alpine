from discord.ext import commands
from typing import Optional
import discord


class ServerManagement(commands.Cog):
    def __init__(self, avi):
        self.avi = avi

    @commands.group()
    async def clone(self, ctx):
        await ctx.send_help("clone")

    @clone.command()
    async def category(self, ctx, category: discord.CategoryChannel, name: Optional[str] = None):
        cloned = await category.clone(name=name)
        message = await ctx.send("Cloning category")
        for channel in category.channels:
            cloned_channel = await channel.clone()
            await message.delete()
            await cloned_channel.edit(category=cloned)
        await ctx.send("Finished cloning category")
        return cloned

    @clone.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        cloned = await channel.clone()
        await ctx.send(f"Cloned channel. Here is the new channel {cloned}")


def setup(avi):
    return
