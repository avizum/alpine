import discord

from discord.ext import commands
from utils import AvimetryBot


class Highlight(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        highlight = ["asd", "dsa"]
        for word in highlight:
            if word in message.content.lower():
                await message.channel.send("Highlight word")
                break


def setup(avi: AvimetryBot):
    return
