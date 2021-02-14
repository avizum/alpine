import discord
from discord.ext import commands
import random
import time
import asyncio

class Counting(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avimetry.user:
            return
        if message.guild is None:
            return
        config_channel=await self.avimetry.config.find(message.guild.id)
        try:
            count_chnl=(config_channel[str("counting_channel")])
        except KeyError:
            return
        
        if message.channel.id == int(count_chnl):
            countdoc=(config_channel[str("current_count")])
            if message.author==self.avimetry.user:
                return
            elif message.author.bot:
                await message.delete()
                return
            elif message.content!=str(countdoc):
                await message.delete()
            else:
                await self.avimetry.config.increment(message.guild.id, 1, "current_count")

    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        if message_after.author == self.avimetry.user:
            return
        config_channel=await self.avimetry.config.find(message_after.guild.id)
        try:
            count_chnl=(config_channel[str("counting_channel")])
        except KeyError:
            return
        if message_after.channel.id == int(count_chnl):
            if message_before.content!=message_after.content:
                await message_after.channel.send("Do not edit your messages to say something else.")
            elif message_before == message_after:
                return

def setup(avimetry):
    avimetry.add_cog(Counting(avimetry))