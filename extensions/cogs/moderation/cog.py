"""
[Avimetry Bot]
Copyright (C) 2021 - 2023 avizum

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

from __future__ import annotations

import datetime as dt
import re
from typing import TYPE_CHECKING

import discord
import humanize
from discord.ext import commands

import core
import utils
from .converters import (
    ModActionFlag,
    BanFlag,
    PurgeAmount,
    TimeConverter,
    TargetMember,
    FindBan,
)
from utils import ModReason, DefaultReason

if TYPE_CHECKING:
    from datetime import datetime
    from core import Bot, Context


class Moderation(core.Cog):
    """
    Moderation commands.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.color: int = 0xF56058
        self.emoji: str = "\U0001f6e1"
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)

    @core.command(hybrid=True)
    @core.has_permissions(kick_members=True)
    @core.bot_has_permissions(kick_members=True)
    @core.describe(target="The person to kick.")
    async def kick(self, ctx: Context, target: TargetMember, *, flags: ModActionFlag):
        """
        Kicks someone from the server.

        You can not kick people with higher permissions than you.
        """
        reason = flags.reason or f"{ctx.author}: No reason provided."
        await target.kick(reason=reason)
        kick_embed = discord.Embed(title="Kicked Member", color=discord.Color.green())
        kick_embed.description = f"**{target}** has been kicked from the server."
        if flags.dm:
            try:
                embed = discord.Embed(
                    title=f"You have been kicked from {ctx.guild.name}",
                    description=f"Reason:\n> {reason}",
                    color=self.color,
                )
                await target.send(embed=embed)
            except discord.Forbidden:
                kick_embed.description = f"**{target}** has been kicked from the server, However, I could not DM them."
        await ctx.send(embed=kick_embed, ephemeral=True)

    @core.command(hybrid=True)
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    @core.describe(targets="The people to kick. (Seperate with spaces.)", reason="Reason that will show up in audit logs.")
    async def masskick(
        self,
        ctx: Context,
        targets: commands.Greedy[TargetMember],
        *,
        reason: ModReason = DefaultReason,
    ):
        """
        Mass kick people from the server.

        You can not kick people with higher permissions than you.
        """
        if not targets:
            return await ctx.send("One or more members can not be kick by you. Try again.", ephemeral=True)
        new_targets = ", ".join(str(i) for i in targets)
        conf = await ctx.confirm(
            message=f"This will kick:\n{new_targets} ({len(targets)} members),\nWith the reason {reason}.",
            confirm_messsage=f'Press "Yes" to kick {(len(targets))} members or "No" to cancel.',
            ephemeral=True,
            delete_message_after=True,
        )
        if conf.result:
            fail = 0
            await conf.message.edit(content="Kicking...")
            for member in targets:
                try:
                    await member.kick(reason=reason)
                except Exception:
                    fail += 1
            await conf.message.edit(content=f"Sucessfully kicked {len(targets)-fail}/{len(targets)} members.")
        else:
            await conf.message.edit(content="Cancelled.")

    @core.command(hybrid=True)
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    @core.describe(target="The person to softban.")
    async def softban(self, ctx: Context, target: TargetMember, *, flags: ModActionFlag):
        """
        Softban someone from the server.

        Softban bans then unbans a person.
        This is like kicking them and deleting their messages.
        You can not softban people with higher permissions than you.
        """
        reason = flags.reason or f"{ctx.author}: No reason provided"
        await ctx.guild.ban(target, reason=reason)
        await ctx.guild.unban(target, reason="Soft-ban")
        soft_ban_embed = discord.Embed(title="Soft-banned Member", color=discord.Color.green())
        soft_ban_embed.description = f"**{target}** has been soft-banned from the server."
        if flags.dm:
            try:
                embed = discord.Embed(
                    title=f"You have been soft-banned from {ctx.guild.name}",
                    description=f"Reason:\n> {reason}",
                    color=self.color,
                )
                await target.send(embed=embed)
            except discord.Forbidden:
                soft_ban_embed.description = f"**{target}** has been soft-banned, However, I could not DM them."
        await ctx.send(embed=soft_ban_embed, ephemeral=True)

    @core.command(hybrid=True)
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    @core.describe(target="The person to ban.")
    async def ban(self, ctx: Context, target: TargetMember, *, flags: BanFlag):
        """
        Ban someone from the server.

        You can ban people whether they are in the server or not.
        You can not ban people with higher permissions than you.
        """
        reason = flags.reason or f"{ctx.author}: No reason provided."
        await ctx.guild.ban(target, reason=reason, delete_message_days=flags.delete_days)
        kick_embed = discord.Embed(title="Banned Member", color=discord.Color.green())
        kick_embed.description = f"**{target}** has been banned from the server."
        if flags.dm:
            try:
                embed = discord.Embed(
                    title=f"You have been banned from {ctx.guild.name}",
                    description=f"Reason:\n> {reason}",
                    color=self.color,
                )
                await target.send(embed=embed)
            except discord.Forbidden:
                kick_embed.description = f"**{target}** has been banned from the server, However, I could not DM them."
        await ctx.send(embed=kick_embed, ephemeral=True)

    @core.command()
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    @core.describe(targets="The people to ban. (Seperate with spaces.)", reason="Reason that will show up in audit logs.")
    async def massban(
        self,
        ctx: Context,
        targets: commands.Greedy[TargetMember],
        *,
        reason: ModReason = DefaultReason,
    ):
        """
        Mass ban people from the server.

        You can not ban people with a role higher than you or higher permissions.
        """
        if not targets:
            return await ctx.send("One or more members can not be banned by you. Try again.", ephemeral=True)
        new_targets = ", ".join(str(i) for i in targets)
        conf = await ctx.confirm(
            message=f"This will ban:\n{new_targets} ({len(targets)} members),\nWith reason {reason}.",
            confirm_messsage=f'Press "Yes" to ban {(len(targets))} members or "No" to cancel.',
            ephemeral=True,
            delete_message_after=True,
        )
        if conf.result:
            fail = 0
            await conf.message.edit(content="Banning...")
            for member in targets:
                try:
                    await member.ban(reason=reason)
                except Exception:
                    fail += 1
            await conf.message.edit(content=f"Sucessfully banned {len(targets)-fail}/{len(targets)} members.")

    @core.command(hybrid=True)
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    @core.describe(target="The person to unban.", reason="The reason for the unban.")
    async def unban(self, ctx: Context, target: FindBan, *, reason: ModReason = DefaultReason):
        """
        Unbans/Removes a ban from someone from the server.

        Anyone with permission to ban members can unban anyone.
        """
        await ctx.guild.unban(target, reason=reason)
        unban_embed = discord.Embed(
            title="Unbanned Member",
            description=f"**{target}** has been unbanned from the server.",
            color=discord.Color.green(),
        )

        await ctx.send(embed=unban_embed)

    @core.command(hybrid=True, aliases=["timeout", "tempmute"])
    @core.has_permissions(moderate_members=True)
    @core.bot_has_permissions(moderate_members=True)
    @core.describe(
        target="The person to mute.",
        duration="The duration of the mute.",
    )
    async def mute(
        self,
        ctx: Context,
        target: TargetMember,
        duration: TimeConverter,
        *,
        reason: ModReason = DefaultReason,
    ):
        """
        Temporarily mutes a member in the server.

        This uses the "Time Out" feature in discord.
        The minimum mute time is 1 minute and the maximum is 28 days. (Discord Limitation.)
        You can not mute people that are higher than you in the role hierarchy.
        """
        if duration > 2419200 or duration < 60:
            return await ctx.send("Mute time must be over 1 minute and under 28 days.", ephemeral=True)
        if target.is_timed_out():
            conf = await ctx.confirm(
                message=f"{target.mention} is already muted. Do you want to overwrite their mute?",
                ephemeral=True,
                delete_message_after=True,
            )
            if not conf.result:
                return await ctx.send("Okay, I won't replace their mute.", delete_after=10, ephemeral=True)
        dur = dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(seconds=duration)
        await target.edit(timed_out_until=dur, reason=reason)
        embed = discord.Embed(
            title="Muted Member",
            description=f"{target.mention} will be muted until {discord.utils.format_dt(dur)}.\nReason: {reason}",
        )
        await ctx.send(embed=embed, ephemeral=True)

    @core.command(hybrid=True, aliases=["untimeout", "untempmute"])
    @core.has_permissions(moderate_members=True)
    @core.bot_has_permissions(moderate_members=True)
    @core.describe(
        target="The person to unmute.",
        reason="The reason for the unmute.",
    )
    async def unmute(self, ctx: Context, target: TargetMember, *, reason: ModReason = DefaultReason):
        """
        Unmutes a member in the server.

        This removes the time out from the member.
        You can not unmute people that are higher than you in the role hierarchy.
        """
        await target.edit(timed_out_until=None, reason=reason)
        await ctx.send(f"Unmuted {target}.", ephemeral=True)

    @core.command(hybrid=True)
    @core.bot_has_permissions(moderate_members=True)
    @core.describe(duration="How long you will be muted for.")
    async def selfmute(self, ctx: Context, duration: TimeConverter):
        """
        Mute yourself for a certain amount of time.
        """
        if ctx.author.top_role > ctx.me.top_role:
            return await ctx.send("I can not mute you because your role is higher than mine.", ephemeral=True)
        if duration > 86400 or duration < 300:
            return await ctx.send("Self mute time must be over 5 minutes and under 1 day.", ephemeral=True)
        dur = dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(seconds=duration)
        conf = await ctx.confirm(
            message=f"Are you sure you want to mute yourself for {utils.format_seconds(duration, friendly=True)}?",
            delete_after=True,
            ephemeral=True,
        )
        if conf.result:
            await ctx.author.edit(timed_out_until=dur, reason=f"Self mute. Expires {dur}")
            embed = discord.Embed(
                title="Self muted",
                description="You have been muted. Do not complain to the moderators about your decision.",
            )
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await conf.message.edit(content="Aborted.")

    async def do_affected(self, messages: list[discord.Message]) -> discord.Embed:
        authors = {}
        for message in messages:
            if message.author not in authors:
                authors[message.author] = 1
            else:
                authors[message.author] += 1
        message = "\n".join(f"{author.mention}: {amount} messages" for author, amount in authors.items())
        if not message:
            message = "No messages deleted."
        return discord.Embed(title="Affected Messages", description=message)

    async def do_purge(self, /, ctx: Context, *args, **kwargs) -> list[discord.Message]:
        async with ctx.typing():
            messages = await ctx.channel.purge(*args, **kwargs)
        return messages

    @core.group(hybrid=True, fallback="messages", invoke_without_command=True)
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.cooldown(5, 30, commands.BucketType.member)
    @core.describe(amount="The amount of messages to purge.")
    async def purge(self, ctx: Context, amount: PurgeAmount):
        """
        Mass delete messages in the current channel.

        This always avoids pinned messages.
        You can only purge up to 1000 messages at a time.
        """
        purged = await self.do_purge(ctx, limit=amount, check=lambda m: not m.pinned, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @purge.command(aliases=["user", "person"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(member="Which member's message to delete.", amount="The amount of messages to purge.")
    async def member(self, ctx: Context, member: discord.Member, amount: PurgeAmount):
        """
        Purge messages from a member.

        You can purge up to 1000 messages from a member.
        """
        purged = await self.do_purge(ctx, limit=amount, check=lambda m: m.author == member, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @purge.command()
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(amount="The amount of messages to purge.")
    async def bots(self, ctx: Context, amount: PurgeAmount):
        """
        Purge any message sent from a bot, including messages sent by me.
        """
        purged = await self.do_purge(ctx, limit=amount, check=lambda m: m.author.bot, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @purge.command()
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(amount="The amount of messages to purge.")
    async def links(self, ctx: Context, amount: PurgeAmount):
        """
        Purge any message that contains a link.
        """

        def check(m: discord.Message):
            return bool(
                re.match(
                    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                    m.content,
                )
            )

        purged = await self.do_purge(ctx, limit=amount, check=check, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @purge.command(aliases=["images", "pictures"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(amount="The amount of messages to purge.")
    async def files(self, ctx: Context, amount: PurgeAmount):
        """
        Purge any message that contains files.
        """
        purged = await self.do_purge(ctx, limit=amount, check=lambda m: m.attachments, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @purge.command(aliases=["in"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(text="The text to purge.")
    async def contains(self, ctx: Context, *, text: str):
        """
        Purge messages containing text.

        This removes up to 100 messages.
        """
        purged = await self.do_purge(ctx, limit=100, check=lambda m: text in m.content, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @purge.command(aliases=["sw", "starts"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(text="The text to purge.")
    async def startswith(self, ctx: Context, *, text: str):
        """
        Purge messages starting with text.

        This removes up to 100 messages.
        """
        purged = await self.do_purge(ctx, limit=100, check=lambda m: m.content.startswith(text))
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @purge.command(aliases=["ew", "ends"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(text="The text to purge.")
    async def endswith(self, ctx: Context, *, text: str):
        """
        Purge messages ending with with text.

        This removes up to 100 messages.
        """
        purged = await self.do_purge(ctx, limit=100, check=lambda m: m.content.endswith(text))
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @core.command(hybrid=True)
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(amount="The amount of messages to remove.")
    async def cleanup(self, ctx: Context, amount: int = 15):
        """
        Delete the last 15 commands.

        Delete messages sent by the bot and users if the message begins with a prefix.
        """
        if not ctx.permissions.manage_messages and amount > 15:
            amount = 15
        base = await self.bot.get_prefix(ctx.message)
        if "" in base:
            base.remove("")
        prefixes = tuple(base)

        def check(message: discord.Message):
            return message.content.startswith(prefixes) or message.author == self.bot.user

        purged = await self.do_purge(ctx, limit=amount, check=check, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @core.group(hybrid=True, invoke_without_command=True)
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def channel(self, ctx: Context):
        """
        Channel management commands.
        """
        await ctx.send_help(ctx.command)

    @channel.command()
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(channel="The channel to lock.", reason="The reason for locking the channel.")
    async def lock(
        self,
        ctx: Context,
        channel: discord.TextChannel = commands.CurrentChannel,
        *,
        reason: ModReason = DefaultReason,
    ):
        """
        Locks a channel.

        This sets the channel overwrite for send messages to Denied.
        """
        await channel.set_permissions(ctx.guild.default_role, send_messages=False, reason=reason)
        lc = discord.Embed(
            title=":lock: Channel Locked.",
            description=f"Channel has been locked.\nReason: {reason}",
            color=discord.Color.red(),
        )
        await ctx.send(f"{utils.Emojis.GREEN_TICK} {channel.mention} locked.")
        if channel != ctx.channel:
            await channel.send(embed=lc)

    @channel.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    @core.describe(channel="The channel to unlock.", reason="The reason for unlocking the channel.")
    async def unlock(
        self,
        ctx: Context,
        channel: discord.TextChannel = commands.CurrentChannel,
        *,
        reason: ModReason = DefaultReason,
    ):
        """
        Unlocks a channel.

        This sets the channel overwrite for send messages to None.
        """
        await channel.set_permissions(ctx.guild.default_role, send_messages=None, reason=reason)
        lc = discord.Embed(
            title=":unlock: Channel Unocked.",
            description=f"Channel has been unlocked.\nReason: {reason}",
            color=discord.Color.green(),
        )
        await ctx.send(f"{utils.Emojis.GREEN_TICK} {channel.mention} unlocked.")
        if channel != ctx.channel:
            await channel.send(embed=lc)

    @channel.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    @core.describe(duration="The duration to slowmode the channel for.")
    async def slowmode(self, ctx: Context, *, duration: TimeConverter):
        """
        Set the channel's slowmode delay.

        The maximum slowmode you can set is 6 hours.
        Setting 0 seconds will disable slowmode.
        """
        if duration > 21600:
            raise commands.BadArgument("Amount should be less than or equal to 6 hours")
        if isinstance(ctx.channel, discord.Thread):
            return await ctx.send("Slowmode delay cannot be set in threads.")
        await ctx.channel.edit(slowmode_delay=duration)  # type: ignore  # not sure why that happens
        embed = discord.Embed(
            title="Changed Slowmode",
            description=f"Slowmode delay has been set to {humanize.precisedelta(duration)}",
        )
        await ctx.send(embed=embed)

    @core.group(hybrid=True, invoke_without_command=True)
    @core.has_permissions(manage_roles=True)
    @core.bot_has_permissions(manage_roles=True)
    async def role(self, ctx: Context):
        """
        Add or remove a role from a member.
        """
        await ctx.send_help("role")

    @role.command(aliases=["append"])
    @core.has_permissions(manage_roles=True)
    @core.bot_has_permissions(manage_roles=True)
    @core.describe(member="The member's roles to modify.", role="The role to add to the member.")
    async def add(self, ctx: Context, member: TargetMember, role: discord.Role):
        """
        Add a role to a member.

        If I can't add a role to them, I will give you a reason why.
        """
        if role >= ctx.me.top_role:
            raise commands.BadArgument("I can't add that role to them.")
        elif role >= ctx.author.top_role:
            raise commands.BadArgument("You can't add that role to them.")
        await member.add_roles(role)
        ra = discord.Embed(
            title="Added Role",
            description=f"Added {role.mention} to {member.mention}.",
        )
        await ctx.send(embed=ra)

    @role.command()
    @core.has_permissions(manage_roles=True)
    @core.bot_has_permissions(manage_roles=True)
    @core.describe(member="The member's roles to modify.", role="The role to add to the member.")
    async def remove(self, ctx: Context, member: TargetMember, role: discord.Role):
        """
        Remove a role from a member.

        If I can't remove that role from them, I will give you a reason why.
        """
        if role >= ctx.me.top_role:
            raise commands.BadArgument("I can't remove that role to them.")
        elif role >= ctx.author.top_role:
            raise commands.BadArgument("You can't remove that role to them.")
        await member.remove_roles(role)
        rr = discord.Embed()
        rr.add_field(
            name="Removed Role",
            value=f"Removed {role.mention} from {member.mention}",
        )
        await ctx.send(embed=rr)

    @core.command(hybrid=True)
    @core.has_permissions(kick_members=True)
    @core.bot_has_permissions(manage_nicknames=True)
    @core.describe(member="The member to nick.", nick="The name to set.")
    async def nick(self, ctx: Context, member: TargetMember, *, nick: str | None = None):
        """
        Gives or chanes a person's nick name.

        I can not edit the server owner and people above me in the role hierarchy.
        I will not let you edit someone higher than you in the role hierarchy.
        """
        if nick is None:
            await member.edit(nick=nick)
        oldnick = member.display_name
        await member.edit(nick=nick)
        newnick = member.display_name
        nickembed = discord.Embed(title="Changed Nickname")
        nickembed.add_field(name="From", value=f"{oldnick}", inline=True)
        nickembed.add_field(name="To", value=f"{newnick}", inline=True)
        await ctx.send(embed=nickembed)
