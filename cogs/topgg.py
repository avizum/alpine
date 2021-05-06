import discord
from utils import AvimetryBot
from discord.ext import commands, tasks


class TopGG(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi
        self.post.start()
        self.update.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != 839892190213439508:
            return
        try:
            user_voted = int(message.content)
        except Exception:
            return
        member = self.avi.get_user(user_voted)
        try:
            await member.send("Thank you for voting!")
        except discord.Forbidden:
            return

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

    @update.before_loop
    async def before_update(self):
        await self.avi.wait_until_ready()


def setup(avi):
    avi.add_cog(TopGG(avi))
