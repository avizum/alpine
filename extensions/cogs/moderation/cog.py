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
import re

import discord
import humanize
from discord.ext import commands

import core
import utils
from core import Bot, Context
from .converters import (
    ModActionFlag,
    BanFlag,
    PurgeAmount,
    TimeConverter,
    TargetMember,
    FindBan,
)
from utils import ModReason, DefaultReason


class Moderation(core.Cog):
    """
    Moderation commands.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.color = 0xF56058
        self.emoji = "\U0001f6e1"
        self.load_time = datetime.datetime.now(datetime.timezone.utc)

    @core.command(hybrid=True)
    @core.both_has_permissions(kick_members=True)
    @core.default_permissions(kick_members=True)
    @core.describe(target="The person to kick.")
    async def kick(self, ctx: Context, target: TargetMember, *, flags: ModActionFlag):
        """
        Kicks someone from the server.

        You can not kick people with higher permissions than you.
        """
        reason = flags.reason or f"{ctx.author}: No reason provided"
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

    @core.command()
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
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
        reason = reason or f"{ctx.author}: No reason provided"
        if not targets:
            return await ctx.send("One or more members can not be kick by you. Try again.")
        new_targets = ", ".join(str(i) for i in targets)
        conf = await ctx.confirm(f"Do you want to kick {new_targets} ({len(targets)} members) with reason {reason}?")
        if conf.result:
            fail = 0
            m = await ctx.send("Kicking...")
            for member in targets:
                try:
                    await member.kick(reason=reason)
                except Exception:
                    fail += 1
            await m.edit(content=f"Sucessfully kicked {len(targets)-fail}/{len(targets)} members.")

    @core.command(hybrid=True)
    @core.both_has_permissions(ban_members=True)
    @core.default_permissions(ban_members=True)
    @core.describe(target="The person to softban.")
    async def softban(self, ctx: Context, target: TargetMember, *, flags: ModActionFlag):
        """
        Softban someone from the server.

        Softban bans then unbans a person.
        This is like kicking them and deleting their messages.
        You can not softban people with higher permissions than you.
        """
        reason = flags.reason or f"{ctx.author}: No reason provided"
        await target.ban(reason=reason)
        await ctx.guild.unban(reason="Soft-ban")
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
    @core.both_has_permissions(ban_members=True)
    @core.default_permissions(ban_members=True)
    @core.describe(target="The person to ban.")
    async def ban(self, ctx: Context, target: TargetMember, *, flags: BanFlag):
        """
        Ban someone from the server.

        You can ban people whether they are in the server or not.
        You can not ban people with higher permissions than you.
        """
        reason = flags.reason or f"{ctx.author}: No reason provided"
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
                kick_embed.description = f"**{target}** has been kicked from the server, However, I could not DM them."
        await ctx.send(embed=kick_embed, ephemeral=True)

    @core.command()
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
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
        reason = reason or f"{ctx.author}: No reason provided"
        if not targets:
            return await ctx.send("One or more members can not be banned by you. Try again.")
        new_targets = ", ".join(str(i) for i in targets)
        conf = await ctx.confirm(f"Do you want to ban {new_targets} ({len(targets)} members) with reason {reason}?")
        if conf.result:
            fail = 0
            m = await ctx.send("Banning...")
            for member in targets:
                try:
                    await member.ban(reason=reason)
                except Exception:
                    fail += 1
            await m.edit(content=f"Sucessfully banned {len(targets)-fail}/{len(targets)} members.")

    @core.command(hybrid=True)
    @core.both_has_permissions(ban_members=True)
    @core.default_permissions(ban_members=True)
    @core.describe(target="The person to unban.", reason="The reason for the unban.")
    async def unban(self, ctx: Context, target: FindBan, *, reason: ModReason = DefaultReason):
        """
        Unbans/Removes a ban from someone from the server.

        Anyone with permission to ban members can unban anyone.
        """
        reason = reason or f"{ctx.author}: No reason provided"
        await ctx.guild.unban(target, reason=reason)
        unban_embed = discord.Embed(
            title="Unbanned Member",
            description=f"**{target}** has been unbanned from the server.",
            color=discord.Color.green(),
        )

        await ctx.send(embed=unban_embed)

    @core.command(hybrid=True, aliases=["timeout", "tempmute"])
    @core.both_has_permissions(moderate_members=True)
    @core.default_permissions(moderate_members=True)
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
        The minumum mute time is 1 second and the maximum is 28 days. (Discord Limitation.)
        You can not mute people that are higher than you in the role hierarchy.
        """
        if duration > 2419200 or duration < 60:
            return await ctx.send("Mute time must be over 1 minute and under 28 days.", ephemeral=True)
        if target.is_timed_out():
            conf = await ctx.confirm(
                f"{target.mention} is already muted. Do you want to overwrite their mute?",
                ephemeral=True, delete_after=True
            )
            if not conf.result:
                return await ctx.send("Okay, I won't replace their mute.", delete_after=10, ephemeral=True)
        reason = reason or f"{ctx.author}: No reason provided."
        dur = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=duration)
        await target.edit(timed_out_until=dur, reason=reason)
        embed = discord.Embed(
            title="Muted Member",
            description=f"{target.mention} will be muted until {discord.utils.format_dt(dur)}.\nReason: {reason}",
        )
        await ctx.send(embed=embed, ephemeral=True)

    @core.command(hybrid=True, aliases=["untimeout", "untempmute"])
    @core.both_has_permissions(moderate_members=True)
    @core.default_permissions(moderate_members=True)
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
        reason = reason or f"{ctx.author}: No reason provided."
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
        dur = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=duration)
        conf = await ctx.confirm(
            f"Are you sure you want to mute yourself for {utils.format_seconds(duration, friendly=True)}?",
            delete_after=True, ephemeral=True
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

    async def do_affected(self, messages: list[discord.Message]):
        authors = {}
        for message in messages:
            if message.author not in authors:
                authors[message.author] = 1
            else:
                authors[message.author] += 1
        message = "\n".join(f"{author.mention}: {amount} messages" for author, amount in authors.items())
        return discord.Embed(title="Affected Messages", description=message)

    async def do_purge(self, /, ctx: Context, *args, **kwargs) -> list[discord.Message]:
        await ctx.defer(ephemeral=True)
        return await ctx.channel.purge(*args, **kwargs)

    @core.group(hybrid=True, fallback="messages", invoke_without_command=True)
    @core.both_has_permissions(manage_messages=True)
    @core.default_permissions(manage_messages=True)
    @core.cooldown(5, 30, commands.BucketType.member)
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
    async def bots(self, ctx: Context, amount: PurgeAmount):
        """
        Purge any message sent from a bot, including me.
        """
        purged = await self.do_purge(ctx, limit=amount, check=lambda m: m.author.bot, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @purge.command()
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
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
    async def files(self, ctx: Context, amount: PurgeAmount):
        """
        Purge any message that contains files.
        """
        purged = await self.do_purge(ctx, limit=amount, check=lambda m: m.attachments, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged), ephemeral=True)

    @purge.command(aliases=["in"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
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

    @core.command(usage="<channel> [reason]")
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def lock(
        self,
        ctx: Context,
        channel: discord.TextChannel,
        *,
        reason: ModReason = DefaultReason,
    ):
        """
        Locks a channel.

        This sets the channel overwrite for send messages to false (x)
        If people can still speak, Set the channel overwrite for send messages to none (/).
        Then set the server permissions for send messages to on.
        If you have any problems, DM Avimetry or ask in the support server.
        """
        reason = reason or f"Action done by {ctx.author}"
        await channel.set_permissions(
            ctx.guild.default_role,
            send_messages=False,
        )
        lc = discord.Embed(
            title=":lock: This channel has been locked.",
            description=f"{ctx.author.mention} has locked down <#{channel.id}> reason: {reason}.",
        )
        await channel.send(embed=lc)

    @core.command(usage="<channel> [reason]")
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def unlock(
        self,
        ctx: Context,
        channel: discord.TextChannel,
        *,
        reason: ModReason = DefaultReason,
    ):
        """
        Unlocks a channel.

        This sets the channel overwrite for send messages to none (/).
        """
        await channel.set_permissions(ctx.guild.default_role, send_messages=None)
        uc = discord.Embed(
            title=":unlock: This channel has been unlocked.",
            description=f"{ctx.author.mention} has unlocked <#{channel.id}> reason: {reason}. ",
        )
        await channel.send(embed=uc)

    @core.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: Context, *, seconds: TimeConverter = 0):
        """
        Set the channel's slowmode delay.

        The maximum slowmode you can set is 6 hours.
        Setting 0 seconds will disable slowmode.
        """
        if seconds > 21600:
            raise commands.BadArgument("Amount should be less than or equal to 6 hours")
        await ctx.channel.edit(slowmode_delay=seconds)
        smembed = discord.Embed(
            title="Changed Slowmode",
            description=f"Slowmode delay has been set to {humanize.precisedelta(seconds)}",
        )
        await ctx.send(embed=smembed)

    @core.group(invoke_without_command=True)
    @core.has_permissions(manage_roles=True)
    @core.bot_has_permissions(manage_roles=True)
    async def role(self, ctx: Context):
        """
        Add or remove a role from a member.
        """
        await ctx.send_help("role")

    @role.command(aliases=["append"])
    @core.has_permissions(manage_roles=True)
    async def add(self, ctx: Context, member: discord.Member, role: discord.Role):
        """
        Add a role to a member.

        If I can't add a role to them, I will give you a reason why.
        """
        await member.add_roles(role)
        ra = discord.Embed(
            title="Added Role",
            description=f"Added {role.mention} to {member.mention}.",
        )
        await ctx.send(embed=ra)

    @role.command()
    @core.has_permissions(manage_roles=True)
    async def remove(self, ctx: Context, member: discord.Member, role: discord.Role):
        """
        Remove a role from a member.

        If I can't remove that role from them, I will give you a reason why.
        """
        await member.remove_roles(role)
        rr = discord.Embed()
        rr.add_field(
            name="Removed Role",
            value=f"Removed {role.mention} from {member.mention}",
        )
        await ctx.send(embed=rr)

    @core.command()
    @core.has_permissions(kick_members=True)
    async def nick(self, ctx: Context, member: TargetMember, *, nick: str = None):
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
