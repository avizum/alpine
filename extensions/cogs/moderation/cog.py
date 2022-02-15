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
from typing import List

import discord
import humanize
from discord.ext import commands

import core
import utils
from utils import (
    AvimetryBot,
    AvimetryContext,
    TimeConverter,
    TargetMember,
    FindBan,
    ModReason,
)


class PurgeAmount(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            number = int(argument)
        except Exception:
            raise commands.BadArgument(
                f"{argument} is not a number. Please give a number."
            )
        if number < 1 or number > 1000:
            raise commands.BadArgument(
                "Number must be greater than 0 and less than 1000"
            )
        return number


class Moderation(core.Cog):
    """
    Moderation commands.
    """

    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.emoji = "\U0001f6e1"
        self.load_time = datetime.datetime.now(datetime.timezone.utc)

    @core.command(usage="<member> [reason]")
    @core.has_permissions(kick_members=True)
    @core.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: AvimetryContext, member: TargetMember, *, reason: ModReason = None):
        """
        Kicks someone from the server.

        You can not kick people with higher permissions than you.
        """
        reason = reason or f"{ctx.author}: No reason provided"
        kick_embed = discord.Embed(title="Kicked Member", color=discord.Color.green())
        await member.kick(reason=reason)
        kick_embed.description = f"**{member}** has been kicked from the server."
        await ctx.send(embed=kick_embed)

    @core.command()
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    async def masskick(self, ctx: AvimetryContext, targets: commands.Greedy[TargetMember], *, reason: ModReason = None):
        """
        Mass kick people from the server.

        You can not kick people with higher permissions than you.
        """
        reason = reason or f"{ctx.author}: No reason provided"
        if not targets:
            return await ctx.send(
                "One or more members can not be kick by you. Try again."
            )
        new_targets = ", ".join(str(i) for i in targets)
        conf = await ctx.confirm(
            f"Do you want to kick {new_targets} ({len(targets)} members) with reason {reason}?"
        )
        if conf.result:
            fail = 0
            m = await ctx.send("Kicking...")
            for member in targets:
                try:
                    await member.kick(reason=reason)
                except Exception:
                    fail += 1
            await m.edit(
                content=f"Sucessfully kicked {len(targets)-fail}/{len(targets)} members."
            )

    @core.command()
    @core.has_permissions(kick_members=True)
    @core.bot_has_permissions(ban_members=True)
    async def softban(self, ctx: AvimetryContext, member: TargetMember, *, reason: ModReason = None):
        """
        Softban someone from the server.

        Softban bans then unbans a person.
        This is like kicking them and deleting their messages.
        You can not softban people with higher permissions than you.
        """
        reason = reason or f"{ctx.author}: No reason provided"
        soft_ban_embed = discord.Embed(
            title="Soft-Banned Member",
            description=f"**{member}** has been soft banned from the server.",
            color=discord.Color.green(),
        )
        await member.ban(reason=reason)
        await ctx.send(embed=soft_ban_embed)

    @core.command(usage="<member> [reason]")
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: AvimetryContext, member: TargetMember, *, reason: ModReason = None):
        """
        Ban someone from the server.

        You can ban people whether they are in the server or not.

        You can not ban people with higher permissions than you.
        """
        reason = reason or f"{ctx.author}: No reason provided"
        ban_embed = discord.Embed(title="Banned Member", color=discord.Color.green())
        if isinstance(member, discord.User):
            await ctx.guild.ban(member, reason=reason)
            ban_embed.description = (
                f"**{str(member)}** has been banned from the server."
            )
            return await ctx.send(embed=ban_embed)

        await member.ban(reason=reason)
        ban_embed.description = f"**{member}** has been banned from the server."
        await ctx.send(embed=ban_embed)

    @core.command()
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    async def massban(self, ctx: AvimetryContext, targets: commands.Greedy[TargetMember], *, reason: ModReason = None):
        """
        Mass ban people from the server.

        You can not ban people with a role higher than you or higher permissions.
        """
        reason = reason or f"{ctx.author}: No reason provided"
        if not targets:
            return await ctx.send(
                "One or more members can not be banned by you. Try again."
            )
        new_targets = ", ".join(str(i) for i in targets)
        conf = await ctx.confirm(
            f"Do you want to ban {new_targets} ({len(targets)} members) with reason {reason}?"
        )
        if conf.result:
            fail = 0
            m = await ctx.send("Banning...")
            for member in targets:
                try:
                    await member.ban(reason=reason)
                except Exception:
                    fail += 1
            await m.edit(
                content=f"Sucessfully banned {len(targets)-fail}/{len(targets)} members."
            )

    @core.command()
    @core.has_permissions(ban_members=True)
    @core.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: AvimetryContext, member: FindBan, *, reason: ModReason = None):
        """
        Unbans/Removes a ban from someone from the server.

        Anyone with permission to ban members can unban anyone.
        """
        reason = reason or f"{ctx.author}: No reason provided"
        await ctx.guild.unban(member, reason=reason)
        unban_embed = discord.Embed(
            title="Unbanned Member",
            description=f"**{member}** has been unbanned from the server.",
            color=discord.Color.green(),
        )

        await ctx.send(embed=unban_embed)

    @core.command(aliases=["timeout", "tempmute"])
    @core.has_permissions(moderate_members=True)
    @core.bot_has_permissions(moderate_members=True)
    async def mute(
        self, ctx: AvimetryContext, member: TargetMember, duration: TimeConverter, *, reason: ModReason = None
    ):
        """
        Temporarily mutes a member in the server.

        This uses the "Time Out" feature in discord.
        The minumum mute time is 1 second and the maximum is 28 days. (Discord Limitation.)
        You can not mute people that are higher than you in the role hierarchy.
        """
        if duration > 2419200 or duration < 60:
            return await ctx.send("Mute time must be over 1 minute and under 28 days.")
        if member.timed_out:
            conf = await ctx.confirm(
                f"{member.mention} is already muted. Do you want to overwrite their mute?",
                delete_after=True,
            )
            if not conf.result:
                return await ctx.send(
                    "Okay, I won't replace their mute.", delete_after=10
                )
        reason = reason or f"{ctx.author}: No reason provided."
        dur = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
            seconds=duration
        )
        await member.edit(timeout_until=dur, reason=reason)
        embed = discord.Embed(
            title="Muted Member",
            description=f"{member.mention} will be muted until {discord.utils.format_dt(dur)}.\nReason: {reason}",
        )
        await ctx.send(embed=embed)

    @core.command(aliases=["untimeout", "untempmute"])
    @core.has_permissions(moderate_members=True)
    @core.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx: AvimetryContext, member: TargetMember, *, reason: ModReason = None):
        """
        Unmutes a member in the server.

        This removes the time out from the member.
        You can not unmute people that are higher than you in the role hierarchy.
        """
        reason = reason or f"{ctx.author}: No reason provided."
        await member.edit(timeout_until=None, reason=reason)
        await ctx.send(f"Unmuted {member}.")

    @core.command()
    @core.bot_has_permissions(moderate_members=True)
    async def selfmute(self, ctx: AvimetryContext, duration: TimeConverter):
        if ctx.author.top_role > ctx.me.top_role:
            return await ctx.send(
                "I can not mute you because your role is higher than mine."
            )
        if duration > 86400 or duration < 300:
            return await ctx.send(
                "Self mute time must be over 5 minutes and under 1 day."
            )
        dur = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
            seconds=duration
        )
        conf = await ctx.confirm(
            f"Are you sure you want to mute yourself for {utils.format_seconds(duration, friendly=True)}?",
            delete_after=True,
        )
        if conf.result:
            await ctx.author.edit(timeout_until=dur, reason=f"Self mute. Expires {dur}")
            embed = discord.Embed(
                title="Self muted",
                description="You have been muted. Do not complain to the moderators about your decision.",
            )
            await ctx.send(embed=embed)
        else:
            await conf.message.edit("Aborted.")

    async def do_affected(self, messages: List[discord.Message]):
        authors = {}
        for message in messages:
            if message.author not in authors:
                authors[message.author] = 1
            else:
                authors[message.author] += 1
        message = "\n".join(
            f"{author.mention}: {amount} messages" for author, amount in authors.items()
        )
        return discord.Embed(title="Affected Messages", description=message)

    @core.group(invoke_without_command=True)
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    @commands.cooldown(5, 30, commands.BucketType.member)
    async def purge(self, ctx: AvimetryContext, amount: PurgeAmount):
        """
        Mass delete messages in the current channel.

        This always avoids pinned messages.
        You can only purge up to 1000 messages at a time.
        """
        purged = await ctx.channel.purge(
            limit=amount, check=lambda m: not m.pinned, before=ctx.message
        )
        await ctx.can_delete(embed=await self.do_affected(purged))

    @purge.command(aliases=["user", "person"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    async def member(self, ctx: AvimetryContext, member: discord.Member, amount: PurgeAmount):
        """
        Purge messages from a member.

        You can purge up to 1000 messages from a member.
        """
        purged = await ctx.channel.purge(
            limit=amount, check=lambda m: m.author == member, before=ctx.message
        )
        await ctx.can_delete(embed=await self.do_affected(purged))

    @purge.command()
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    async def bots(self, ctx: AvimetryContext, amount: PurgeAmount):
        """
        Purge any message sent from a bot, including me.
        """
        purged = await ctx.channel.purge(
            limit=amount, check=lambda m: m.author.bot, before=ctx.message
        )
        await ctx.can_delete(embed=await self.do_affected(purged))

    @purge.command()
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    async def contains(self, ctx: AvimetryContext, *, text):
        """
        Purge messages containing text.

        This removes up to 100 messages.
        """
        purged = await ctx.channel.purge(
            limit=100, check=lambda m: text in m.content, before=ctx.message
        )
        await ctx.can_delete(embed=await self.do_affected(purged))

    @purge.command(aliases=["sw", "starts"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    async def startswith(self, ctx: AvimetryContext, *, text):
        """
        Purge messages starting with text.

        This removes up to 100 messages.
        """
        purged = await ctx.channel.purge(
            limit=100, check=lambda m: m.content.startswith(text)
        )
        await ctx.can_delete(embed=await self.do_affected(purged))

    @purge.command(aliases=["ew", "ends"])
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    async def endswith(self, ctx: AvimetryContext, *, text):
        """
        Purge messages ending with with text.

        This removes up to 100 messages.
        """
        purged = await ctx.channel.purge(
            limit=100, check=lambda m: m.content.endswith(text)
        )
        await ctx.can_delete(embed=await self.do_affected(purged))

    @core.command(usage="[amount]")
    @core.has_permissions(manage_messages=True)
    @core.bot_has_permissions(manage_messages=True)
    async def cleanup(self, ctx: AvimetryContext, amount=15):
        """
        Delete the last 15 commands.

        Delete messages sent by the bot and users if the message begins with a prefix.
        """
        base = await self.bot.get_prefix(ctx.message)
        if "" in base:
            base.remove("")
        prefixes = tuple(base)

        def check(message: discord.Message):
            return (
                message.content.startswith(prefixes) or message.author == self.bot.user
            )

        purged = await ctx.channel.purge(limit=amount, check=check, before=ctx.message)
        await ctx.can_delete(embed=await self.do_affected(purged))

    @core.command(usage="<channel> [reason]")
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx: AvimetryContext, channel: discord.TextChannel, *, reason: ModReason = None):
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
            description=f"{ctx.author.mention} has locked down <#{channel.id}> with the reason of {reason}."
        )
        await channel.send(embed=lc)

    @core.command(usage="<channel> [reason]")
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx: AvimetryContext, channel: discord.TextChannel, *, reason="No Reason Provided"):
        """
        Unlocks a channel.

        This sets the channel overwrite for send messages to none (/).
        """
        await channel.set_permissions(ctx.guild.default_role, send_messages=None)
        uc = discord.Embed(
            title=":unlock: This channel has been unlocked.",
            description=f"{ctx.author.mention} has unlocked <#{channel.id}> with the reason of {reason}. "
        )
        await channel.send(embed=uc)

    @core.command()
    @core.has_permissions(manage_channels=True)
    @core.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: AvimetryContext, *, seconds: TimeConverter = 0):
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
            description=f"Slowmode delay has been set to {humanize.precisedelta(seconds)}"
        )
        await ctx.send(embed=smembed)

    @core.group(invoke_without_command=True)
    @core.has_permissions(manage_roles=True)
    @core.bot_has_permissions(manage_roles=True)
    async def role(self, ctx: AvimetryContext):
        """
        Add or remove a role from a member.
        """
        await ctx.send_help("role")

    @role.command(aliases=["append"])
    @core.has_permissions(manage_roles=True)
    async def add(self, ctx: AvimetryContext, member: discord.Member, role: discord.Role):
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
    async def remove(self, ctx: AvimetryContext, member: discord.Member, role: discord.Role):
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
    async def nick(self, ctx: AvimetryContext, member: TargetMember, *, nick=None):
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
        nickembed = discord.Embed(
            title="Changed Nickname"
        )
        nickembed.add_field(name="From", value=f"{oldnick}", inline=True)
        nickembed.add_field(name="To", value=f"{newnick}", inline=True)
        await ctx.send(embed=nickembed)


def setup(bot: AvimetryBot):
    bot.add_cog(Moderation(bot))