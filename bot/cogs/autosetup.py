from discord.ext import commands
import logging

logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


class GuildJoin(commands.Cog, name="Auto Setup"):
    def __init__(self, avi):
        self.avi = avi

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.avi.temp.cache_new_guild(guild.id)
        channel = self.avi.get_channel(829812033946910720)
        await channel.send(f"Joined a server **{guild.name}** with **{guild.member_count}** members")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        channel = self.avi.get_channel(829812033946910720)
        await channel.send(f"Left {guild.name} with {guild.member_count} members")


def setup(avi):
    avi.add_cog(GuildJoin(avi))
