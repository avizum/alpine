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
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)

        prefixes[str(guild.id)] = "a."

        with open("./avimetrybot/files/prefixes.json", "w") as f:
            json.dump(prefixes, f, indent=4)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)

        prefixes.pop(str(guild.id))

        with open("./avimetrybot/files/prefixes.json", "w") as f:
            json.dump(prefixes, f, indent=4)

def setup(avimetry):
    avimetry.add_cog(ServerPrefix(avimetry))
