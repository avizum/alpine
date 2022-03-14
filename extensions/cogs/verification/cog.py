"""
Handle verification gating (if enabled)
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

import asyncio
import datetime
import random
import string

import discord

import core
from core import Bot, Context


class MemberJoin(core.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.messages = {}

    async def do_verify(self, member):
        prefix = await self.bot.cache.get_guild_settings(member.guild.id)
        prefixes = prefix.get("prefixes")
        pre = prefixes[0] if prefixes else "a."

        config = self.bot.cache.verification.get(member.guild.id)
        role = config.get("role_id")
        high = config.get("high")

        if not config or not role or not high:
            return

        if config["high"] is True:
            if config["role_id"] is None:
                return

            channel = member.guild.get_channel(config.get("channel_id"))
            x = discord.Embed(
                title=f"Welcome to **{member.guild.name}**!",
                description=(
                    f"Hey {member.mention}, welcome to the server!\n"
                    f"Please use `{pre}verify` to verify. Enter the key you recieve in your DMs here."
                ),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                color=discord.Color.green(),
            )
            message = await channel.send(
                f"{member.mention}",
                embed=x,
                allowed_mentions=discord.AllowedMentions(users=True),
            )
            try:
                self.messages[member.id] = message
            except KeyError:
                pass

    @core.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        if member.pending:
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
        await ctx.message.delete()
        member = ctx.author
        config = self.bot.cache.verification.get(member.guild.id)
        if not config:
            return
        role = ctx.guild.get_role(config.get("role_id"))
        channel = ctx.guild.get_channel(config.get("channel_id"))
        if not role or not channel or role in member.roles:
            return
        letters = string.ascii_letters
        randomkey = "".join(random.choice(letters) for i in range(10))

        try:
            await member.send(
                f"**Here is your key. Send it in {ctx.channel.mention}. This key will expire in one minute.**"
            )
            await member.send(f"{randomkey}")
        except discord.Forbidden:
            keyforbidden = discord.Embed()
            keyforbidden.add_field(
                name="Please turn on your DMs and run the `verify` command again.",
                value="User Settings > Privacy & Safety > Allow direct messages from server members",
            )
            return await ctx.send(embed=keyforbidden)

        sent_dms = discord.Embed(
            title="I sent a key to your DMs",
            description="Please enter your key here to complete the verification process.",
        )
        send_message = await ctx.send(embed=sent_dms)

        def check(m):
            return m.author == ctx.author and m.channel == channel

        while True:
            try:
                msg = await self.bot.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                timeup = discord.Embed(
                    title="Your Key has expired",
                    description=(
                        "Sorry, your key has expired. If you want to generate a new key, "
                        f"use the command `{ctx.clean_prefix}verify` to generate a new key."
                    ),
                )
                await ctx.author.send(embed=timeup)
                break
            else:
                if msg.content != randomkey:
                    await msg.delete(delay=5)
                    pass
                else:
                    await send_message.delete()
                    message = self.messages.get(member.id)
                    if message:
                        await message.delete()
                    await msg.delete(delay=5)
                    await member.add_roles(role)
                    break
