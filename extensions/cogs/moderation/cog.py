"""
[Alpine Bot]
Copyright (C) 2021 - 2024 avizum

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
from typing import TYPE_CHECKING

import discord
import humanize
from discord.ext import commands

import core
import utils
from utils import DefaultReason, EMOJI_REGEX, format_list, ModReason, timestamp

from .converters import BanFlag, FindBan, ModActionFlag, PurgeAmount, TargetMember, TimeConverter

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

        message = f"Kicked {target}."
        if flags.dm:
            try:
                embed = discord.Embed(
                    title=f"You have been kicked from {ctx.guild.name}",
                    description=f"Reason:\n> {reason}",
                    color=self.color,
                )
                await target.send(embed=embed)
            except discord.Forbidden:
                message = f"Kicked {target}. I could not DM them."
        await ctx.send(message)

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
            remove_view_after=True,
        )
        if conf.result:
            fail = 0
            await conf.message.edit(content="Kicking...")
            kicked: list[discord.Member] = []
            for member in targets:
                try:
                    await member.kick(reason=reason)
                    kicked.append(member)
                except Exception:
                    fail += 1
            kicked_fmt = format_list(kicked)
            return await conf.message.edit(
                content=f"Sucessfully kicked {kicked_fmt} ({len(targets)-fail}/{len(targets)}) members."
            )
        return await conf.message.edit(content="Cancelled.")

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
        message = f"Soft-banned {target}."
        if flags.dm:
            try:
                embed = discord.Embed(
                    title=f"You have been soft-banned from {ctx.guild.name}",
                    description=f"Reason:\n> {reason}",
                    color=self.color,
                )
                await target.send(embed=embed)
            except discord.Forbidden:
                message = f"Soft-banned {target}. I could not DM them."
        await ctx.send(message)

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
        message = f"Banned {target}."
        if flags.dm:
            try:
                embed = discord.Embed(
                    title=f"You have been banned from {ctx.guild.name}",
                    description=f"Reason:\n> {reason}",
                    color=self.color,
                )
                await target.send(embed=embed)
            except discord.Forbidden:
                message = f"Banned {target}. I could not DM them."
        await ctx.send(message)

    @core.command()
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    @core.describe(targets="The people to ban. (Seperate with spaces.)", reason="Reason that will show up in audit logs.")
    async def massban(
        self,
        ctx: Context,
        targets: commands.Greedy[discord.Member],
        *,
        reason: ModReason = DefaultReason,
    ):
        """
        Mass ban people from the server.

        You can not ban people with a role higher than you or higher permissions.
        """
        if len(targets) == 0:
            raise commands.MissingRequiredArgument(ctx.command.params["targets"])

        convert = TargetMember.convert
        converted: list[discord.Member] = []
        conversion_errors: dict[discord.Member, str] = {}
        for target in targets:
            try:
                # when conversion fails, it will show the action as ban, not massban as that makes more sense for the user.
                ctx.invoked_with = "ban"
                conv_target = await convert(ctx, target.name)
                converted.append(conv_target)
            except commands.BadArgument as bad_arg:
                conversion_errors[target] = str(bad_arg)

        if conversion_errors:
            cont = await ctx.confirm(
                message=(
                    "The following members can not be banned:\n```"
                    f"{"\n".join(f"{mem}: {rsn}" for mem, rsn in conversion_errors.items())}```"
                ),
                confirm_messsage="Would you like to continue?",
                delete_message_after=True,
            )
            if cont.result is False:
                return

        conf = await ctx.confirm(
            message=f"This will ban:\n{format_list(converted)} ({len(converted)} members),\nWith reason {reason}",
            confirm_messsage=f'Press "Yes" to ban {(len(converted))} members or "No" to cancel.',
        )

        if conf.result:
            await conf.message.edit(content=f"Banning {(len(converted))} members...", view=None)
            result = await ctx.guild.bulk_ban(converted, reason=reason)
            banned_members = [mem for ban_objs in result.banned for mem in converted if ban_objs.id == mem.id]
            await conf.message.edit(
                content=f"Sucessfully banned {format_list(banned_members)} ({len(banned_members)}/{len(converted)}) members."
            )
        else:
            await conf.message.edit(content="Cancelled.", view=None)

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

        await ctx.send(f"Unbanned {target}.")

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
            f"{target.mention} is already muted. Do you want to continue?"
            conf = await ctx.confirm(
                message=f"{target.mention} is already muted. Do you want to continue?",
                ephemeral=True,
                remove_view_after=True,
            )
            if not conf.result:
                return await conf.message.edit(content="Okay, cancelled.", delete_after=10)
        dur = dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(seconds=duration)
        await target.edit(timed_out_until=dur, reason=reason)
        return await ctx.send(f"Muted {target} until {timestamp(dur)}.\nReason: {reason}", ephemeral=True)

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

    async def _affected(self, messages: list[discord.Message]) -> discord.Embed:
        authors = {}
        for message in messages:
            if message.author not in authors:
                authors[message.author] = 1
            else:
                authors[message.author] += 1
        message = (
            "\n".join(f"{author.mention}: {amount} messages" for author, amount in authors.items()) or "No messages deleted"
        )
        return discord.Embed(title="Affected Messages", description=message)

    async def _purge(self, /, ctx: Context, *args, **kwargs) -> list[discord.Message]:
        async with ctx.typing(ephemeral=True):
            return await ctx.channel.purge(*args, **kwargs)

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
        purged = await self._purge(ctx, limit=amount, check=lambda m: not m.pinned, before=ctx.message)
        await ctx.can_delete(embed=await self._affected(purged), ephemeral=True)

    @purge.command(aliases=["user", "person"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(member="Which member's message to delete.", amount="The amount of messages to purge.")
    async def member(self, ctx: Context, member: discord.Member, amount: PurgeAmount):
        """
        Purge messages from a member.

        You can purge up to 1000 messages from a member.
        """
        purged = await self._purge(ctx, limit=amount, check=lambda m: m.author == member, before=ctx.message)
        await ctx.can_delete(embed=await self._affected(purged), ephemeral=True)

    @purge.command()
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(amount="The amount of messages to purge.")
    async def bots(self, ctx: Context, amount: PurgeAmount):
        """
        Purge any message sent from a bot, including messages sent by me.
        """
        purged = await self._purge(ctx, limit=amount, check=lambda m: m.author.bot, before=ctx.message)
        await ctx.can_delete(embed=await self._affected(purged), ephemeral=True)

    @purge.command()
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(amount="The amount of messages to purge.")
    async def links(self, ctx: Context, amount: PurgeAmount):
        """
        Purge any message that contains a link.
        """

        def check(m: discord.Message):
            return bool(EMOJI_REGEX.findall(m.content))

        purged = await self._purge(ctx, limit=amount, check=check, before=ctx.message)
        await ctx.can_delete(embed=await self._affected(purged), ephemeral=True)

    @purge.command(aliases=["images", "pictures"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(amount="The amount of messages to purge.")
    async def files(self, ctx: Context, amount: PurgeAmount):
        """
        Purge any message that contains files.
        """
        purged = await self._purge(ctx, limit=amount, check=lambda m: m.attachments, before=ctx.message)
        await ctx.can_delete(embed=await self._affected(purged), ephemeral=True)

    @purge.command(aliases=["in"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(text="The text to purge.")
    async def contains(self, ctx: Context, *, text: str):
        """
        Purge messages containing text.

        This removes up to 100 messages.
        """
        purged = await self._purge(ctx, limit=100, check=lambda m: text in m.content, before=ctx.message)
        await ctx.can_delete(embed=await self._affected(purged), ephemeral=True)

    @purge.command(aliases=["sw", "starts"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(text="The text to purge.")
    async def startswith(self, ctx: Context, *, text: str):
        """
        Purge messages starting with text.

        This removes up to 100 messages.
        """
        purged = await self._purge(ctx, limit=100, check=lambda m: m.content.startswith(text))
        await ctx.can_delete(embed=await self._affected(purged), ephemeral=True)

    @purge.command(aliases=["ew", "ends"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @core.describe(text="The text to purge.")
    async def endswith(self, ctx: Context, *, text: str):
        """
        Purge messages ending with with text.

        This removes up to 100 messages.
        """
        purged = await self._purge(ctx, limit=100, check=lambda m: m.content.endswith(text))
        await ctx.can_delete(embed=await self._affected(purged), ephemeral=True)

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

        purged = await self._purge(ctx, limit=amount, check=check, before=ctx.message)
        await ctx.can_delete(embed=await self._affected(purged), ephemeral=True)

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
        return await ctx.send(embed=embed)

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
        if role >= ctx.author.top_role:
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
        if role >= ctx.author.top_role:
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
