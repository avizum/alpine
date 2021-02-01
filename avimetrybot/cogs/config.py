import discord
import os
import asyncio
import json
from discord.ext import commands, tasks
from itertools import cycle
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

class serverprefix(commands.Cog, name="server prefix"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.avimetry.config.upsert({"_id":guild.id, "prefix":"a."})

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.avimetry.config.unset({"_id":guild})

    

def setup(avimetry):
    avimetry.add_cog(serverprefix(avimetry))
