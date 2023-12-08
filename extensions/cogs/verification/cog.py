"""
Handle verification gating (if enabled)
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

import asyncio
import datetime as dt
import random
import string
from typing import TYPE_CHECKING

import discord

import core

if TYPE_CHECKING:
    from datetime import datetime

    from core import Bot, Context


class MemberJoin(core.Cog):
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)
        self.messages: dict[int, discord.Message] = {}

    async def do_verify(self, member: discord.Member):
        settings = self.bot.database.get_guild(member.guild.id)
        if not settings:
            return
        verification = settings.verification
        if not verification:
            return

        prefix = settings.prefixes[0] if settings.prefixes else "a."
        role = member.guild.get_role(verification.role_id)
        channel = member.guild.get_channel(verification.channel_id)
        enabled = verification.high
        if not enabled or not role or not channel:
            return

        embed = discord.Embed(
            title=f"Welcome to {member.guild.name}!",
            description=(
                f"Hey {member.mention}, you need to verify before you are able to see the channels.\n"
                f"Use `{prefix}verify` to get started."
            ),
            timestamp=dt.datetime.now(dt.timezone.utc),
            color=discord.Color.green(),
        )

        assert isinstance(channel, discord.TextChannel)

        message = await channel.send(member.mention, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
        self.messages[member.id] = message

    @core.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot or member.pending:
            return
        await self.do_verify(member)

    @core.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        message = self.messages.get(member.id)
        if message:
            try:
                await message.delete()
            except discord.NotFound:
                pass

    @core.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.pending is True and after.pending is False:
            await self.do_verify(after)

    @core.command(hidden=True)
    @core.bot_has_permissions(manage_messages=True, manage_roles=True)
    async def verify(self, ctx: Context):
        """
        Verify.

        This command only works if the server has verification enabled.
        """
        member = ctx.author

        guild = ctx.database.get_guild(ctx.guild.id)
        if not guild:
            return
        verification = guild.verification
        if not verification:
            return
        role = ctx.guild.get_role(verification.role_id)
        channel = ctx.guild.get_channel(verification.channel_id)
        if not role or not channel or role in member.roles:
            return

        key = "".join(random.choice(string.ascii_letters) for _ in range(10))

        try:
            await member.send(f"Here is your key. Send it in {ctx.channel.mention}.")
            await member.send(key)
        except discord.Forbidden:
            return await ctx.send("I can not send you the code. Please enabled your DMs and try again.")

        sent_to_dms = await ctx.channel.send(
            "A key was sent to your DMs. Copy and paste the key here to continue.",
        )

        def check(message: discord.Message) -> bool:
            return message.author == member and message.channel == ctx.channel and message.content == key

        try:
            message: discord.Message = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            return await ctx.author.send(f"Timed out. Run `{ctx.prefix}verify` to continue.")
        else:
            await ctx.message.delete()
            await sent_to_dms.delete()
            to_delete = self.messages.get(ctx.author.id)
            if to_delete:
                await to_delete.delete()
            await message.delete()
            await ctx.author.add_roles(role)
