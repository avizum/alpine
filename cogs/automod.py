import discord
from discord.ext import commands
import random
import asyncio
import json
import datetime

class AutoMod(commands.Cog):
    
    def __init__(self, avibot):
        self.avibot = avibot
        self.mc = commands.CooldownMapping.from_cooldown(5, 8, commands.BucketType.member)
        self.coold = commands.CooldownMapping.from_cooldown(0, 1, commands.BucketType.member)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avibot.user:
            return
        if message.author.bot:
            return
        
        with open("files/badword.json", "r") as f:
            blacklist = json.load(f)

        for words in blacklist:
            if words in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, don't say that word!", delete_after=3)


    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        if message_before.author == self.avibot.user:
            return
        
        with open("files/badword.json", "r") as f:
            blacklist = json.load(f)

        for words in blacklist:
            if words in message_after.content.lower():
                await message_after.delete()
                await message_after.channel.send(f"{message_after.author.mention}, don't edit your message to say that word!", delete_after=3)

    

def setup(avibot):
    avibot.add_cog(AutoMod(avibot))


