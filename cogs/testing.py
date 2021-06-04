
from utils import AvimetryBot, AvimetryContext
from discord.ext import commands


class Testing(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    @commands.command()
    async def checks(self, ctx: AvimetryContext):
        c = self.avi.get_command("ban")
        for check in c.checks:
            try:
                check(ctx)
            except Exception as e:
                print(e)


def setup(avi: AvimetryBot):
    avi.add_cog(Testing(avi))
