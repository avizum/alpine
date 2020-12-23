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
        if message.content == '<@!756257170521063444>':
            with open("files/prefixes.json", "r") as f:
                prefixes = json.load(f)

            pre = prefixes[str(message.guild.id)]
            await message.channel.send(f"Hey, {message.author.mention}, my prefix is `{pre}`")
        if message.channel.id == 787942299854045184:
            with open("files/prefixes.json", "r") as f:
                prefixes = json.load(f)

            pre = prefixes[str(message.guild.id)]
            if message.content.startswith(f"{pre}requestnick"):
                if message.content.endswith('"'):
                    es = "<:aviSuccess:777096731438874634>"
                    await message.add_reaction(es)
                else:
                    em = "<:aviError:777096756865269760>"
                    await message.add_reaction(em)
                    we = discord.Embed()
                    we.add_field(name="<:aviError:777096756865269760> Wrong Format", value=f'Use `{pre}requestnick "nick name in quotation marks"` to request for a new nick name.')
                    await message.channel.send(embed=we, delete_after=15)
            else:
                em = "<:aviError:777096756865269760>"
                await message.add_reaction(em)
                we = discord.Embed()
                we.add_field(name="<:aviError:777096756865269760> Wrong Format", value=f'Use `{pre}requestnick "nick name in quotation marks"` to request for a new nick name.')
                await message.channel.send(embed=we, delete_after=15)

        
def setup(avibot):
    avibot.add_cog(AutoResponder(avibot))
