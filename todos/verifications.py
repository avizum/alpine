import discord
#  import string
#  import random
#  import asyncio
#  import datetime
from discord.ext import commands
from utils.context import AvimetryContext


class JoinGate(commands.Cog):
    def __init__(self, avi):
        self.avi = avi

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        try:
            config = self.avi.cache.guild_settings[member.guild.id]
            prefix = config["prefixes"][0]
        except KeyError:
            prefix = "a."
        print(prefix)

    @commands.command()
    async def verify(self, ctx: AvimetryContext):
        return
