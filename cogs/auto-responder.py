import discord
from discord.ext import commands
import random
import time
import asyncio
import json

class AutoResponder(commands.Cog):

    def __init__(self, avibot):
        self.avibot = avibot

    #If Bot is pinged it responds with prefix
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avibot.user:
            return
        if message.content == '<@!756257170521063444>':
            with open("files/prefixes.json", "r") as f:
                prefixes = json.load(f)
            pre = prefixes[str(message.guild.id)]
            await message.channel.send(f"Hey, {message.author.mention}, my prefix is `{pre}`")
        
def setup(avibot):
    avibot.add_cog(AutoResponder(avibot))
