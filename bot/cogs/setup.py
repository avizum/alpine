import logging
from discord.ext import commands, tasks


logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


class Setup(commands.Cog):
    def __init__(self, avi):
        self.avi = avi
        self.recache.start()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.avi.temp.cache_new_guild(guild.id)
        channel = self.avi.get_channel(829812033946910720)
        await channel.send(f"Joined a server named **{guild.name}** with **{guild.member_count}** members")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel = self.avi.get_channel(829812033946910720)
        await channel.send(f"Left a server named **{guild.name}** with **{guild.member_count}** members")

    @tasks.loop(hours=1)
    async def recache(self):
        await self.avi.temp.cache_all()

    @recache.before_loop
    async def before_reacache(self):
        await self.avi.wait_until_ready()


def setup(avi):
    avi.add_cog(Setup(avi))
