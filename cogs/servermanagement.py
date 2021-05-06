import discord
from typing import Union
from discord.ext import commands
from utils.context import AvimetryContext


class ServerManagement(commands.Cog, name="Server Management"):
    def __init__(self, avi):
        self.avi = avi

    @commands.command(
        aliases=["members", "mc"], brief="Gets the members of the server and shows you."
    )
    async def membercount(self, ctx: AvimetryContext):
        tmc = len([m for m in ctx.guild.members if not m.bot])
        tbc = len([m for m in ctx.guild.members if m.bot])
        amc = ctx.guild.member_count
        mce = discord.Embed(title=f"Member Count for {ctx.guild.name}")
        mce.add_field(name="Members:", value=f"{tmc} members", inline=False)
        mce.add_field(name="Bots:", value=f"{tbc} bots", inline=False)
        mce.add_field(name="Total Members:", value=f"{amc} members", inline=False)
        await ctx.send(embed=mce)

    @commands.group(
        invoke_without_command=True
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def channel(self, ctx):
        await ctx.send_help("channel")

    @channel.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def clone(self, ctx: AvimetryContext,
                    channel: Union[discord.CategoryChannel,
                                   discord.TextChannel,
                                   discord.VoiceChannel,
                                   discord.StageChannel]):
        if isinstance(channel, discord.CategoryChannel):
            new = await channel.clone()
            for channels in channel.channels:
                thing = await channels.clone(reason="because")
                await thing.edit(category=new)
            return await ctx.send(f"Successfully cloned {channel.mention}.")
        await channel.clone(reason="because")
        await ctx.send(f"Successfully cloned {channel.mention}.")

    @channel.command()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def delete(self, ctx: AvimetryContext, channel: Union[discord.CategoryChannel,
                                                                discord.TextChannel,
                                                                discord.VoiceChannel,
                                                                discord.StageChannel]):

        conf = await ctx.confirm(f"Are you sure you want to delete {channel.mention}?")
        if conf:
            return await ctx.channel.delete()
        return


def setup(avi):
    avi.add_cog(ServerManagement(avi))
