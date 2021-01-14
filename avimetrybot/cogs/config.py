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
        g_id = str(guild.id)
        def_pre = {g_id: "a."}
        self.avimetry.collection.update_one({"_id":"prefixes"}, {"$set":def_pre})

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        g_id = str(guild.id)
        rem_pre = {g_id: ""}
        self.avimetry.collection.update_one({"_id":"prefixes"}, {"$unset":rem_pre})

def setup(avimetry):
    avimetry.add_cog(ServerPrefix(avimetry))
