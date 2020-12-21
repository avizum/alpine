import discord
from discord.ext import commands
import random
import asyncio
import json

class AutoMod(commands.Cog):
    
    def __init__(self, avibot):
        self.avibot = avibot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avibot.user:
            return
        
        with open("files/badword.json", "r") as f:
            blacklist = json.load(f)

        for words in blacklist:
            if words in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, don't say that word!", delete_after=3)

def setup(avibot):
    avibot.add_cog(AutoMod(avibot))


