
import discord
from utils import AvimetryBot, AvimetryContext
from discord.ext import commands


class Testing(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    @commands.command()
    async def message(self, ctx: AvimetryContext, message: discord.Message):
        await message.reply("asd")


def setup(avi: AvimetryBot):
    avi.add_cog(Testing(avi))
