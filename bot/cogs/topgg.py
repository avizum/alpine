import discord
from discord.ext import commands, tasks


class TopGG(commands.Cog):
    def __init__(self, avi):
        self.avi = avi
        self.post.start()

    @tasks.loop(minutes=15)
    async def post(self):
        if self.avi.user.id != 756257170521063444:
            return
        await self.avi.topgg.post_guild_count(len(self.avi.guilds))

    @post.before_loop
    async def before_post(self):
        await self.avi.wait_until_ready()

    @tasks.loop(minutes=30)
    async def update(self):
        if self.avi.user.id != 756257170521063444:
            return
        status = discord.Status.online
        game = discord.Game(f"@Avimetry | {len(self.avi.guilds)} Servers")
        await self.avi.change_presence(status=status, activity=game)


def setup(avi):
    avi.add_cog(TopGG(avi))
