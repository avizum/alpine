import discord
from discord.ext import commands
import random
import time
import asyncio
import json

class AutoResponder(commands.Cog):

    def __init__(self, avibot):
        self.avibot = avibot

#Auto Responder
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avibot.user:
            return
        rcwords=['no u', 'nou', 'no you', 'noyou', 'u no']
        if message.content.lower() in rcwords:
            emoji="<:reverse_card:752008998080741377>"
            await message.add_reaction(emoji)
        lolwords=['lol','haha', 'harhar', 'har har']
        if message.content.lower() in lolwords:
            emoji="😂"
            await message.add_reaction(emoji)
        coffinword=['rip', 'r i p', 'wrip', 'oof']
        if message.content.lower() in coffinword:
            emoji='⚰'
            await message.add_reaction(emoji)
        if message.content == '<@!756257170521063444>':
            with open("files/prefixes.json", "r") as f:
                prefixes = json.load(f)

            pre = prefixes[str(message.guild.id)]
            await message.channel.send(f"Hey, {message.author.mention}, my prefix is `{pre}`")

        
def setup(avibot):
    avibot.add_cog(AutoResponder(avibot))
