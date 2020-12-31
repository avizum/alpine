import discord
from discord.ext import commands

class MemberCount(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry=avimetry

    @commands.Cog.listener()
    async def on_member_join(self, member):
        refchan = self.avimetry.get_channel(783961111060938782)
        if member.guild.id == refchan.guild.id:
            channel = self.avimetry.get_channel(783961111060938782)
            await channel.edit(name=f"Total Members: {member.guild.member_count}")
        
            channel2 = self.avimetry.get_channel(783960970472456232)
            true_member_count = len([m for m in member.guild.members if not m.bot])
            await channel2.edit(name=f"Members: {true_member_count}")

            channel3 = self.avimetry.get_channel(783961050814611476)
            true_bot_count = len([m for m in member.guild.members if m.bot])
            await channel3.edit(name=f"Bots: {true_bot_count}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        lrefchan = self.avimetry.get_channel(783961111060938782)
        if member.guild.id == lrefchan.guild.id:
            channel = self.avimetry.get_channel(783961111060938782)
            await channel.edit(name=f"Total Members: {member.guild.member_count}")
            
            channel2 = self.avimetry.get_channel(783960970472456232)
            true_member_count = len([m for m in member.guild.members if not m.bot])
            await channel2.edit(name=f"Members: {true_member_count}")

            channel3 = self.avimetry.get_channel(783961050814611476)
            true_bot_count = len([m for m in member.guild.members if m.bot])
            await channel3.edit(name=f"Bots: {true_bot_count}")

    @commands.command(aliases=["updatemc", "umembercount"], brief="Updates the member count if the count gets out of sync.")
    async def updatemembercount(self, ctx):
        channel = self.avimetry.get_channel(783961111060938782)
        await channel.edit(name=f"Total Members: {channel.guild.member_count}")
        
        channel2 = self.avimetry.get_channel(783960970472456232)
        true_member_count = len([m for m in channel.guild.members if not m.bot])
        await channel2.edit(name=f"Members: {true_member_count}")

        channel3 = self.avimetry.get_channel(783961050814611476)
        true_bot_count = len([m for m in channel.guild.members if m.bot])
        await channel3.edit(name=f"Bots: {true_bot_count}")
        await ctx.send("Member Count Updated.")
#Update Member Count Command
    @commands.command(aliases=["members", "mc"], brief="Gets the members of the server and shows you.")
    async def membercount(self, ctx):
        tmc = len([m for m in ctx.guild.members if not m.bot])
        tbc = len([m for m in ctx.guild.members if m.bot])
        amc = ctx.guild.member_count
        mce = discord.Embed(title=f"Member Count for {ctx.guild.name}")
        mce.add_field(name="Members:", value=f"{tmc} members", inline=False)
        mce.add_field(name="Bots:", value=f"{tbc} bots", inline=False)
        mce.add_field(name="Total Members:", value=f"{amc} members", inline=False)
        await ctx.send(embed=mce)

def setup(avimetry):
    avimetry.add_cog(MemberCount(avimetry))