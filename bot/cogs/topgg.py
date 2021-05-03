from discord.ext import commands


class TopGG(commands.Cog):
    def __init__(self, avi):
        self.avi = avi

    @commands.Cog.listener()
    async def on_guild_post(self):
        print("Posted")


def setup(avi):
    avi.add_cog(TopGG(avi))

