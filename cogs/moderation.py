"""
Powerful commands to help moderators with moderating.
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
import asyncio
import datetime
import humanize

from discord.ext import commands
from utils import (
    AvimetryBot, AvimetryContext, TimeConverter, TargetMemberAction, FindBan, ModReason)


class Moderation(commands.Cog):
    """
    Moderation commands.
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot

    @commands.command(brief="Kicks a member from the server.", usage="<member> [reason]")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: AvimetryContext, member: TargetMemberAction, *, reason: ModReason = None):
        kick_embed = discord.Embed(
            title="Kicked Member",
            color=discord.Color.green()
        )
        await member.kick(reason=reason)
        kick_embed.description = f"**{member}** has been kicked from the server."
        await ctx.send(embed=kick_embed)

    @commands.command(brief="Bans then unbans a member from the server")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def softban(self, ctx: AvimetryContext, member: TargetMemberAction, *, reason: ModReason = None):
        soft_ban_embed = discord.Embed(
            title="Soft-Banned Member",
            description=f"**{member}** has been soft banned from the server.",
            color=discord.Color.green()
        )
        await member.ban(reason=reason)
        await ctx.send(embed=soft_ban_embed)

    @commands.command(brief="Bans a member from the server", usage="<member> [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: AvimetryContext, member: TargetMemberAction, *, reason: ModReason = None):
        ban_embed = discord.Embed(
            title="Banned Member",
            color=discord.Color.green()
        )
        if isinstance(member, discord.User):
            await ctx.guild.ban(member, reason=reason)
            ban_embed.description = f"**{str(member)}** has been banned from the server."
            return await ctx.send(embed=ban_embed)

        await member.ban(reason=reason)
        ban_embed.description = f"**{str(member)}** has been banned from the server."
        await ctx.send(embed=ban_embed)

    @commands.command(brief="Unbans a member from the server.", usage="<member_id> [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: AvimetryContext, member: FindBan, *, reason: ModReason = None):
        await ctx.guild.unban(member, reason=reason)
        unban_embed = discord.Embed(
            title="Unbanned Member",
            description=f"**{str(member)}** has been unbanned from the server.",
            color=discord.Color.green()
        )
        await ctx.send(embed=unban_embed)

    @commands.command(
        brief="Mutes a person indefinitely"
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx: AvimetryContext, member: TargetMemberAction, *, reason: ModReason = None):
        role = await ctx.cache.get_guild_settings(ctx.guild.id)
        mute_role = ctx.guild.get_role(role["mute_role"])
        await member.add_roles(mute_role, reason=reason)
        await ctx.send(f"{member.mention} has been muted indefinitely.")

    @commands.command(
        brief="Temporarily mute someone for a specified amount of time.",
        enabled=False
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def tempmute(
        self, ctx: AvimetryContext, member: TargetMemberAction, time: TimeConverter, *, reason: ModReason = None
    ):
        print(f"Mute: {member}, {time}, {reason}")

    @commands.group(
        invoke_without_command=True,
        brief="Mass delete a number of messages in the current channel.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(5, 30, commands.BucketType.member)
    async def purge(self, ctx: AvimetryContext, amount: int):
        if amount < 1:
            return
        authors = {}

        def check(message: discord.Message):
            return not message.pinned

        purged = await ctx.channel.purge(limit=amount, check=check, before=ctx.message)
        for message in purged:
            if message.author not in authors:
                authors[message.author] = 1
            else:
                authors[message.author] += 1
        await asyncio.sleep(0.1)
        msg = "\n".join(
            f"{author.mention}: {amount} {'message' if amount == 1 else 'messages'}"
            for author, amount in authors.items()
        )

        pe = discord.Embed(
            title="Affected Messages",
            description=f"{msg}")
        await ctx.can_delete(embed=pe)

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def match(self, ctx: AvimetryContext, amount: int, *, text):
        await ctx.message.delete()

        def pmatch(m):
            return text in m.content

        await ctx.channel.purge(limit=amount, check=pmatch)
        purgematch = discord.Embed()
        purgematch.add_field(
            name="<:yesTick:777096731438874634> Purge Match",
            value=f"Purged {amount} messages containing {text}.",
        )

    @commands.command(brief="Delete bot messages", usage="[amount]")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def cleanup(self, ctx: AvimetryContext, amount=15):
        prefixes = tuple(await self.bot.get_prefix(ctx.message))

        def check(message: discord.Message):
            return message.content.startswith(prefixes) or message.author == self.bot.user

        purged = await ctx.channel.purge(limit=amount, check=check, before=ctx.message)

        authors = {}
        for message in purged:
            if message.author not in authors:
                authors[message.author] = 1
            else:
                authors[message.author] += 1
        await asyncio.sleep(0.1)
        msg = "\n".join(
            f"{author.mention}: {amount} {'message' if amount == 1 else 'messages'}"
            for author, amount in authors.items()
        )

        pe = discord.Embed(
            title="Affected Messages",
            description=f"{msg}")
        await ctx.can_delete(embed=pe)

    @commands.command(
        brief="Locks the mentioned channel.",
        usage="<channel> [reason]",
        timestamp=datetime.datetime.utcnow())
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx: AvimetryContext, channel: discord.TextChannel, *, reason="No Reason Provided"):
        await channel.set_permissions(
            ctx.guild.default_role, send_messages=False,
        )
        lc = discord.Embed()
        lc.add_field(
            name=":lock: Channel has been locked.",
            value=f"{ctx.author.mention} has locked down <#{channel.id}> with the reason of {reason}. \
            Only Staff members can speak now.",
        )
        await channel.send(embed=lc)

    @commands.command(
        brief="Unlocks the mentioned channel.",
        usage="<channel> [reason]",
        timestamp=datetime.datetime.utcnow(),
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx: AvimetryContext, channel: discord.TextChannel, *, reason="No Reason Provided"):
        await channel.set_permissions(
            ctx.guild.default_role, send_messages=None)
        uc = discord.Embed()
        uc.add_field(
            name=":unlock: Channel has been unlocked.",
            value=f"{ctx.author.mention} has unlocked <#{channel.id}> with the reason of {reason}. \
            Everyone can speak now.",
        )
        await channel.send(embed=uc)

    @commands.command(brief="Sets the slowmode in the current channel.")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: AvimetryContext, *, seconds: TimeConverter = 0):
        if seconds > 21600:
            raise commands.BadArgument("Amount should be less than or equal to 6 hours")
        await ctx.channel.edit(slowmode_delay=seconds)
        smembed = discord.Embed()
        smembed.add_field(
            name="<:yesTick:777096731438874634> Set Slowmode",
            value=f"Slowmode delay is now set to {humanize.precisedelta(seconds)}.",
        )
        await ctx.send(embed=smembed)

    @commands.group(invoke_without_command=True, brief="The command you just called")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx: AvimetryContext):
        await ctx.send_help("role")

    @role.command(brief="Give a role to a member.")
    @commands.has_permissions(manage_roles=True)
    async def add(self, ctx: AvimetryContext, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        ra = discord.Embed()
        ra.add_field(
            name="<:yesTick:777096731438874634> Role Add",
            value=f"Added {role.mention} to {member.mention}.",
        )
        await ctx.send(embed=ra)

    @role.command(brief="Remove a role from a member.")
    @commands.has_permissions(manage_roles=True)
    async def remove(self, ctx: AvimetryContext, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        rr = discord.Embed()
        rr.add_field(
            name="<:yesTick:777096731438874634> Role Remove",
            value=f"Removed {role.mention} from {member.mention}",
        )
        await ctx.send(embed=rr)

    @commands.command(brief="Changes a member's nickname.")
    @commands.has_permissions(kick_members=True)
    async def nick(self, ctx: AvimetryContext, member: TargetMemberAction, *, nick=None):
        if nick is None:
            await member.edit(nick=nick)
        oldnick = member.display_name
        await member.edit(nick=nick)
        newnick = member.display_name
        nickembed = discord.Embed(
            title="<:yesTick:777096731438874634> Nickname Changed"
        )
        nickembed.add_field(name="Old Nickname", value=f"{oldnick}", inline=True)
        nickembed.add_field(name="New Nickname", value=f"{newnick}", inline=True)
        await ctx.send(embed=nickembed)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def selfban(self, ctx: AvimetryContext):
        conf = await ctx.confirm("Are you sure you want to ban yourself?")
        if conf:
            return await ctx.send("Sike")

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def selfkick(self, ctx: AvimetryContext):
        conf = await ctx.confirm("Are you sure you want to kick yourself?")
        if conf:
            return await ctx.send("Sike")


def setup(bot):
    bot.add_cog(Moderation(bot))
