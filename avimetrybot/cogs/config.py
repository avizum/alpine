import discord
import os
import asyncio
import json
from discord.ext import commands, tasks
from itertools import cycle

class ServerPrefix(commands.Cog, name="Server Prefix"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.avimetry.config.upsert({"_id":guild.id, "prefix":"a."})

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.avimetry.config.unset({"_id":guild})

    

def setup(avimetry):
    avimetry.add_cog(ServerPrefix(avimetry))
