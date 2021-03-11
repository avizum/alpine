from discord.ext import commands
from utils.errors import AvizumsLoungeOnly


class AvizumsLounge(commands.Cog, name="Avizum's Lounge"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    def cog_check(ctx):
        if ctx.guild.id != 751490725555994716:
            raise AvizumsLoungeOnly
        return True

    # Counter
    @commands.Cog.listener()
    async def on_member_join(self, member):
        refchan = self.avimetry.get_channel(783961111060938782)
        try:
            if member.guild.id == refchan.guild.id:
                channel = self.avimetry.get_channel(783961111060938782)
                await channel.edit(name=f"Total Members: {member.guild.member_count}")

                channel2 = self.avimetry.get_channel(783960970472456232)
                true_member_count = len([m for m in member.guild.members if not m.bot])
                await channel2.edit(name=f"Members: {true_member_count}")

                channel3 = self.avimetry.get_channel(783961050814611476)
                true_bot_count = len([m for m in member.guild.members if m.bot])
                await channel3.edit(name=f"Bots: {true_bot_count}")
        except Exception:
            return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        lrefchan = self.avimetry.get_channel(783961111060938782)
        try:
            if member.guild.id == lrefchan.guild.id:
                channel = self.avimetry.get_channel(783961111060938782)
                await channel.edit(name=f"Total Members: {member.guild.member_count}")

                channel2 = self.avimetry.get_channel(783960970472456232)
                true_member_count = len([m for m in member.guild.members if not m.bot])
                await channel2.edit(name=f"Members: {true_member_count}")

                channel3 = self.avimetry.get_channel(783961050814611476)
                true_bot_count = len([m for m in member.guild.members if m.bot])
                await channel3.edit(name=f"Bots: {true_bot_count}")
        except Exception:
            return

    # Update Member Count Command
    @commands.command(
        aliases=["updatemc", "umembercount"],
        brief="Updates the member count if the count gets out of sync.",
    )
    @commands.has_permissions(administrator=True)
    async def refreshcount(self, ctx):
        channel = self.avimetry.get_channel(783961111060938782)
        await channel.edit(name=f"Total Members: {channel.guild.member_count}")

        channel2 = self.avimetry.get_channel(783960970472456232)
        true_member_count = len([m for m in channel.guild.members if not m.bot])
        await channel2.edit(name=f"Members: {true_member_count}")

        channel3 = self.avimetry.get_channel(783961050814611476)
        true_bot_count = len([m for m in channel.guild.members if m.bot])
        await channel3.edit(name=f"Bots: {true_bot_count}")
        await ctx.send("Member Count Updated.")


def setup(avimetry):
    avimetry.add_cog(AvizumsLounge(avimetry))
