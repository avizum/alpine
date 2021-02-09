import discord
from discord.ext import commands
import random
import asyncio
import json
import datetime

class automod(commands.Cog, name="auto moderation"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

'''
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avimetry.user:
            return
        if message.author.bot:
            return
        with open("./avimetrybot/files/badword.json", "r") as f:
            blacklist = json.load(f)

        for words in blacklist:
            if words in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, don't say that word!", delete_after=3)
                
    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        if message_before.author == self.avimetry.user:
            return
        
        with open("./avimetrybot/files/badword.json", "r") as f:
            blacklist = json.load(f)

        for words in blacklist:
            if words in message_after.content.lower():
                await message_after.delete()
                await message_after.channel.send(f"{message_after.author.mention}, don't edit your message to say that word!", delete_after=3)
'''
def setup(avimetry):
    avimetry.add_cog(automod(avimetry)) #40