import discord
from discord.ext import commands

class AvimetryMessage(discord.Message):

    async def edit(self, content=None, embed: discord.Embed=None, *args, **kwargs):
        if content:
            print("content")