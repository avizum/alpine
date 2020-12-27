import discord
import os
import asyncio
import json
from discord.ext import commands, tasks
from itertools import cycle

class ServerPrefix(commands.Cog):
    def __init__(self, avibot):
        self.avibot = avibot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with open("avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)

        prefixes[str(guild.id)] = "a."

        with open("avimetrybot/files/prefixes.json", "w") as f:
            json.dump(prefixes, f, indent=4)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with open("avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)

        prefixes.pop(str(guild.id))

        with open("avimetrybot/files/prefixes.json", "w") as f:
            json.dump(prefixes, f, indent=4)

    @commands.command(brief="Set the prefix of the server.")
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, nprefix):
        with open("avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)

        prefixes[str(ctx.guild.id)] = nprefix

        with open("avimetrybot/files/prefixes.json", "w") as f:
            json.dump(prefixes, f, indent=4)
        
        cp=discord.Embed()
        cp.add_field(
            name="<:aviSuccess:777096731438874634> Set Prefix",
            value=f"The prefix for **{ctx.guild.name}** is now `{nprefix}`"
        )
        await ctx.send(embed=cp)
    @setprefix.error
    async def setprefixErr(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            nopperm=discord.Embed()
            nopperm.add_field(name="<:aviError:777096756865269760> No Permission", value="You do not have have the required permissions to use the `a.setprefix` command.", inline=False)
            await ctx.send(embed=nopperm)

def setup(avibot):
    avibot.add_cog(ServerPrefix(avibot))
