
from utils import AvimetryBot, AvimetryContext
from discord.ext import commands


class Testing(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    @commands.command()
    async def checks(self, ctx: AvimetryContext):
        await ctx.send("check")


def setup(avi: AvimetryBot):
    avi.add_cog(Testing(avi))
