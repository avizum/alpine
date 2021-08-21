"""
Commands to manage your server (Limited, Might Remove.)
Copyright (C) 2021 avizum

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
import datetime
import core

from typing import Union
from discord.ext import commands
from utils import AvimetryBot, AvimetryContext, ModReason


class ServerManagement(commands.Cog, name="Server Management"):
    """
    Commands to manage your server.
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)

    @core.group(aliases=["members", "mc"])
    async def membercount(self, ctx: AvimetryContext):
        """
        Show the member count.
        """
        tmc = len([m for m in ctx.guild.members if not m.bot])
        tbc = len([m for m in ctx.guild.members if m.bot])
        amc = ctx.guild.member_count
        mce = discord.Embed(title=f"Member Count for {ctx.guild.name}")
        mce.add_field(name="Members:", value=f"{tmc} members", inline=False)
        mce.add_field(name="Bots:", value=f"{tbc} bots", inline=False)
        mce.add_field(name="Total Members:", value=f"{amc} members", inline=False)
        await ctx.send(embed=mce)

    @membercount.command()
    async def role(self, ctx: AvimetryContext, role: discord.Role):
        """
        Show the members in a role.
        """
        tmc = sum(not m.bot for m in role.members)
        tbc = sum(m.bot for m in role.members)
        mce = discord.Embed(title=f"Members in role: {role}")
        mce.add_field(name="Members:", value=f"{tmc} members", inline=False)
        mce.add_field(name="Bots:", value=f"{tbc} bots", inline=False)
        mce.add_field(name="Members", value=", ".join(i.mention for i in role.members[:42]))
        await ctx.send(embed=mce)

    @core.group(invoke_without_command=True)
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def channel(self, ctx):
        """
        Manage channels in the server.

        You can create channels,
        clone channels,
        or delete channels.
        """
        await ctx.send_help(ctx.command)

    @channel.group(invoke_without_command=True)
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def create(self, ctx: AvimetryContext):
        """
        Creates a channel.

        This command does nothing on it's own. Use the subcommands for full functionality.
        """
        await ctx.send_help(ctx.command)

    @create.command(aliases=["tc", "text", "textchannel", "text-channel"])
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def text_channel(self, ctx: AvimetryContext, name):
        """
        Creates a text chanel.

        This doesn't set any permissions, This may be added soon.
        """
        channel = await ctx.guild.create_text_channel(name)
        await ctx.send(f"Created channel {channel.mention}.")

    @create.command(aliases=["vc", "voice", "voicechannel", "voice-channel"])
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def voice_channel(self, ctx: AvimetryContext, name):
        channel = await ctx.guild.create_voice_channel(name)
        await ctx.send(f"Created channel {channel.mention}.")

    @create.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def category(self, ctx: AvimetryContext, name):
        """
        Creates a category.

        This doesn't set any permissions, This may be added soon.
        """
        channel = await ctx.guild.create_text_channel(name)
        await ctx.send(f"Created category channel {channel.mention}.")

    @channel.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def clone(self, ctx: AvimetryContext, channel: Union[discord.CategoryChannel,
                                                               discord.TextChannel,
                                                               discord.VoiceChannel,
                                                               discord.StageChannel]):
        """
        Clones a channel.

        This clones the channel with all the permissions.
        """
        if isinstance(channel, discord.CategoryChannel):
            new = await channel.clone()
            for channels in channel.channels:
                thing = await channels.clone(reason="because")
                await thing.edit(category=new)
            return await ctx.send(f"Successfully cloned {channel.mention}.")
        await channel.clone(reason="because")
        await ctx.send(f"Successfully cloned {channel.mention}.")

    @channel.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def delete(self, ctx: AvimetryContext, channel: Union[discord.CategoryChannel,
                                                                discord.TextChannel,
                                                                discord.VoiceChannel,
                                                                discord.StageChannel]):
        """
        Deletes a channel.

        This asks for confirmation to prevent abuse.
        """
        conf = await ctx.confirm(f"Are you sure you want to delete {channel.mention}?")
        if conf:
            return await ctx.channel.delete()
        return await conf.message.edit(content='Aborted.')

    @core.command(aliases=["steal-emoji", "stealemoji"])
    @core.has_permissions(manage_emojis=True)
    @core.bot_has_permissions(manage_emojis=True)
    async def steal_emoji(self, ctx: AvimetryContext, emoji: discord.PartialEmoji, *, reason: ModReason = None):
        """
        Steal an emoji.

        This creates an emoji with the same name.
        You can provide a reason.
        """
        reason = reason or f"{ctx.author}: No reason provided"
        asset = await emoji.url.read()
        await ctx.guild.create_custom_emoji(name=emoji.name, image=asset, reason=reason)

    @core.command()
    @core.has_permissions(manage_roles=True)
    @core.bot_has_permissions(manage_roles=True)
    async def create_role(self, ctx: AvimetryContext, name: str, color: discord.Color = None, reason: ModReason = None):
        """
        Creates a role.

        Create a role with the name, color.
        """
        reason = reason or f"{ctx.author}: No reason provided"
        await ctx.guild.create_role(name=name, color=color, reason=reason)


def setup(bot):
    bot.add_cog(ServerManagement(bot))
