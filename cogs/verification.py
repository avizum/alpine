"""
Handle verification gating (if enabled)
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
import string
import random
import asyncio
import datetime

from utils import AvimetryBot, AvimetryContext
from discord.ext import commands


class MemberJoin(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    async def do_verify(self, member):
        prefix = await self.avi.cache.get_guild_settings(member.guild.id)
        pre = "a." if not prefix["prefixes"] else prefix["prefixes"][0]

        config = self.avi.cache.verification.get(member.guild.id)

        if not config:
            return

        if config["low"] is True:
            return
        if config["medium"] is True:
            return
        if config["high"] is True:
            name = "New Members"
            category = discord.utils.get(member.guild.categories, name=name)
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            }
            await member.guild.create_text_channel(
                f"{member.name.lower().replace(' ', '-')}-verification",
                category=category,
                reason=f"Started Verification for {member.name}",
                overwrites=overwrites,
            )

            channel = discord.utils.get(
                member.guild.channels, name=f"{member.name.lower().replace(' ', '-')}-verification",
            )
            x = discord.Embed(
                title=f"Welcome to **{member.guild.name}**!",
                description=(
                    f"Hey {member.mention}, welcome to the server!\n"
                    f"Please use `{pre}verify` to verify. Enter the key you recieve in your DMs here."
                ),
                timestamp=datetime.datetime.utcnow(),
                color=discord.Color.green()
            )
            await channel.send(
                f"{member.mention}", embed=x,
                allowed_mentions=discord.AllowedMentions(
                    users=True
                ),
            )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        if member.pending:
            return
        await self.do_verify(member)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.pending is True and after.pending is False:
            await self.do_verify(after)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        dchnl = discord.utils.get(member.guild.channels, name=f"{member.name.lower().replace(' ', '-')}-verification")
        if dchnl in member.guild.channels:
            await dchnl.delete(reason=f"{member.name} left during verification")

    @commands.command(brief="Verify now!", hidden=True)
    async def verify(self, ctx: AvimetryContext):
        member = ctx.author
        config = self.avi.cache.verification.get(member.guild.id)
        if not config:
            return await ctx.send("Please setup verification.")
        role_id = ctx.guild.get_role(config["role_id"])

        channel = discord.utils.get(
            ctx.guild.channels,
            name=f"{member.name.lower().replace(' ', '-')}-verification",
        )

        if not channel:
            return
        letters = string.ascii_letters
        randomkey = "".join(random.choice(letters) for i in range(10))

        try:
            rkey = discord.Embed()
            rkey.add_field(
                name="Here is your key. Your key will expire after 1 minute of inactivity.",
                value=f"`{randomkey}`",
            )
            if member.is_on_mobile():
                await member.send("**Here is your key. Your key will expire after 1 minute of inactivity.**")
                await member.send(f"{randomkey}")
            else:
                await member.send(embed=rkey)

        except discord.Forbidden:
            keyforbidden = discord.Embed()
            keyforbidden.add_field(
                name="Please turn on your DMs and run the `verify` command again.",
                value="User Settings > Privacy & Safety > Allow direct messages from server members",
            )
            return await ctx.send(embed=keyforbidden)

        ksid = discord.Embed(
            title="I sent a key to your DMs",
            description="Please enter your key here to complete the verification process."
        )
        await ctx.send(embed=ksid)
        channel = ctx.channel

        def check(m):
            return m.author == ctx.author and m.channel == channel

        while True:
            try:
                msg = await self.avi.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                timeup = discord.Embed(
                    title="Your Key has expired",
                    description=(
                        "Sorry, your key has expired. If you want to generate a new key, "
                        f"use the command `{ctx.clean_prefix}.verify` to generate a new key."
                    )
                )
                await ctx.author.send(embed=timeup)
                break
            else:
                if msg.content != randomkey:
                    await ctx.send("Wrong Key, Try again.")
                else:
                    verembed = discord.Embed(
                        title="Verification complete!",
                        description="Congratulations, you have been verified! Please wait while I update your roles...",
                    )
                    await ctx.send(embed=verembed)
                    await member.add_roles(role_id)
                    cnl = discord.utils.get(
                        ctx.guild.channels, name=f"{member.name.lower().replace(' ', '-')}-verification",
                    )
                    try:
                        await cnl.delete(reason=f"{member.name} finished verification")
                    except Exception:
                        pass
                    break


def setup(avi):
    avi.add_cog(MemberJoin(avi))
