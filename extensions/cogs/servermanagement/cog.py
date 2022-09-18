"""
[Avimetry Bot]
Copyright (C) 2021 - 2022 avizum

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

import datetime

import discord
from discord.ext import commands

import core
from core import Bot, Context
from utils import ModReason, DefaultReason


class ServerManagement(commands.Cog, name="Server Management"):
    """
    Commands to manage your server.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.emoji = "<:server:913309745073504307>"

    @core.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        if before.id not in self.bot.cache.guild_settings[before.guild.id]["auto_unarchive"]:
            return

        if before.archived is False and after.archived is True:
            await after.edit(archived=False)

    @core.group(invoke_without_command=True)
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def channels(self, ctx):
        """
        Manage channels in the server.

        You can create channels,
        clone channels,
        or delete channels.
        """
        await ctx.send_help(ctx.command)

    @channels.group(invoke_without_command=True)
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def create(self, ctx: Context):
        """
        Creates a channel.

        This command does nothing on it's own. Use the subcommands for full functionality.
        """
        await ctx.send_help(ctx.command)

    @create.command(aliases=["tc", "text", "textchannel", "text-channel"])
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def text_channel(self, ctx: Context, name):
        """
        Creates a text chanel.

        This doesn't set any permissions, This may be added soon.
        """
        channel = await ctx.guild.create_text_channel(name)
        await ctx.send(f"Created channel {channel.mention}.")

    @create.command(aliases=["vc", "voice", "voicechannel", "voice-channel"])
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def voice_channel(self, ctx: Context, name):
        channel = await ctx.guild.create_voice_channel(name)
        await ctx.send(f"Created channel {channel.mention}.")

    @create.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def category(self, ctx: Context, name):
        """
        Creates a category.

        This doesn't set any permissions, This may be added soon.
        """
        channel = await ctx.guild.create_text_channel(name)
        await ctx.send(f"Created category channel {channel.mention}.")

    @channels.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def clone(self, ctx: Context, channel: discord.abc.GuildChannel):
        """
        Clones a channel.

        This clones the channel with all the permissions.
        """
        if isinstance(channel, discord.CategoryChannel):
            new = await channel.clone()
            for channels in channel.channels:
                thing = await channels.clone(reason="Clone")
                await thing.edit(category=new)  # type: ignore  # still don't know why that happens
            return await ctx.send(f"Successfully cloned {channel.mention}.")
        await channel.clone(reason="because")
        await ctx.send(f"Successfully cloned {channel.mention}.")

    @channels.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def delete(self, ctx: Context, channel: discord.abc.GuildChannel):
        """
        Deletes a channel.

        This asks for confirmation to prevent abuse.
        """
        conf = await ctx.confirm(message=f"Are you sure you want to delete {channel.mention}?")
        if conf:
            return await ctx.channel.delete()
        return await conf.message.edit(content="Aborted.")

    @core.command(aliases=["steal-emoji", "stealemoji"])
    @core.has_permissions(manage_emojis=True)
    @core.bot_has_permissions(manage_emojis=True)
    async def steal_emoji(
        self,
        ctx: Context,
        emoji: discord.PartialEmoji,
        *,
        reason: ModReason = DefaultReason,
    ):
        """
        Steal an emoji.

        This creates an emoji with the same name.
        You can provide a reason.
        """
        asset = await emoji.read()
        await ctx.guild.create_custom_emoji(name=emoji.name, image=asset, reason=reason)

    @core.command()
    @core.has_permissions(manage_roles=True)
    @core.bot_has_permissions(manage_roles=True)
    async def create_role(
        self,
        ctx: Context,
        name: str,
        color: discord.Color,
        reason: ModReason = DefaultReason,
    ):
        """
        Creates a role.

        Create a role with the name, color.
        """
        r = await ctx.guild.create_role(name=name, color=color, reason=reason)
        await ctx.send(f"Created {r}")
