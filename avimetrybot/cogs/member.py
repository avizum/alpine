import discord
from discord.ext import commands


class MemberManagement(commands.Cog, name="Member Management"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    # Member Count
    @commands.command(
        aliases=["members", "mc"], brief="Gets the members of the server and shows you."
    )
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
    avimetry.add_cog(MemberManagement(avimetry))
