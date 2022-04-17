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

import discord
import datetime
import asyncio
import base64
import re
from io import BytesIO

from discord.ext import tasks
from core import Bot
from asyncgist import File

import core

TOKEN_REGEX = r"([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84})"


class BotLogs(core.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.clear_cache.start()

    @core.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if (
            not message.guild
            or message.author == self.bot.user
            or message.author.id == 80528701850124288
            or message.guild.id == 336642139381301249
        ):
            return
        tokens = re.findall(TOKEN_REGEX, message.content)
        if tokens:
            split_token = tokens[0].split(".")
            try:
                user_bytes = split_token[0].encode()
                user_id_decoded = base64.b64decode(user_bytes)
                user_id_decoded.decode("ascii")
            except Exception:
                if not split_token[0].startswith("mfa"):
                    return

            gist = await self.bot.gist.post_gist(
                description="Tokens found.", files=File(filename="tokens.txt", content="\n".join(tokens)), public=True
            )
            embed = discord.Embed(
                description=(
                    f"Hey {message.author.name}, "
                    "I found Discord authentication tokens in your message. "
                    f"It was [uploaded to a Gist.]({gist.html_url})\n"
                ),
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)
            mentions = discord.AllowedMentions.all()
            if message.guild is None:
                return
            await message.reply(embed=embed, allowed_mentions=mentions, mention_author=True)

    @core.Cog.listener("on_message_delete")
    @core.Cog.listener("on_bulk_message_delete")
    async def logging_delete(self, message: discord.Message | list[discord.Message]):
        try:
            data = self.bot.cache.logging.get(message.guild.id)
        except AttributeError:
            data = self.bot.cache.logging.get(message[0].guild.id)
        if not data or data["enabled"] is not True or not data.get("message_delete") or not data.get("channel_id"):
            return
        channel = self.bot.get_channel(data["channel_id"])
        if isinstance(message, discord.Message):
            context = await self.bot.get_context(message)
            if context.valid or not message.guild:
                return
            if message.author == self.bot.user or message.author.bot:
                return
            embed = discord.Embed(
                title="Message Delete",
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                description=f"Message from {message.author.mention} deleted in {message.channel.mention}",
                color=discord.Color.red(),
            )
            embed.set_footer(text="Deleted at")
            if message.content:
                embed.add_field(name="Deleted content", value=f">>> {message.content}")
            if not message.content:
                return
        if isinstance(message, list):
            list_of_messages = []
            for m in message:
                timestamp = discord.utils.format_dt(m.created_at, "t")
                content = m.content[:90] or "*No content*"
                list_of_messages.append(f"[{timestamp}] {m.author}: {content}")
            if not list_of_messages:
                return
            embed = discord.Embed(
                title="Bulk Message Delete",
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                color=discord.Color.red(),
            )
            embed.set_footer(text=f"{len(message)} deleted")
            messages = "\n\n----------\n\n".join(list_of_messages)
            if len(messages) > 4000:
                message_file = discord.File(filename="messages.txt", fp=BytesIO(messages.encode("utf-8")))
                return await channel.send(embed=embed, file=message_file)
            embed.description = "\n".join(list_of_messages)
        return await channel.send(embed=embed)

    @core.Cog.listener("on_message_edit")
    async def logging_edit(self, before: discord.Message, after: discord.Message):
        context = await self.bot.get_context(after)
        if context.valid:
            return
        if before.guild is None and after.guild is None:
            return
        data = self.bot.cache.logging.get(before.guild.id)
        if not data or data["enabled"] is not True or not data.get("message_edit") or not data.get("channel_id"):
            return
        if before.author == self.bot.user or before.author.bot:
            return
        if before.content == after.content:
            return
        bef_con = f"{before.content[:1017]}..." if len(before.content) > 1024 else before.content

        aft_con = f"{after.content[:1017]}..." if len(after.content) > 1024 else after.content

        embed = discord.Embed(
            title="Message Edit",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            description=f"Message was edited by {before.author.mention} in {before.channel.mention}",
        )
        embed.add_field(name="Before", value=f">>> {bef_con}", inline=False)
        embed.add_field(name="After", value=f">>> {aft_con}", inline=False)
        embed.set_footer(text="Edited at")
        channel = self.bot.get_channel(data["channel_id"])
        await channel.send(embed=embed)

    @core.Cog.listener("on_member_ban")
    async def logging_ban(self, guild: discord.Guild, user: discord.User):
        data = self.bot.cache.logging.get(guild.id)
        if not data or data["enabled"] is not True or not data.get("member_ban") or not data.get("channel_id"):
            return
        await asyncio.sleep(2)
        entry = [entry async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban)][0]
        if entry.target == user:
            channel = self.bot.get_channel(data["channel_id"])
            embed = discord.Embed(
                title="Member Banned",
                description=f"{user} ({user.id}) has been banned from {guild.name}.",
                color=discord.Color.red(),
            )
            embed.add_field(name="Responsible Moderator:", value=entry.user, inline=False)
            embed.add_field(name="Ban Reason:", value=entry.reason, inline=False)
            embed.set_thumbnail(url=user.display_avatar.url)
            await channel.send(embed=embed)

    @core.Cog.listener("on_member_remove")
    async def loggging_kick(self, member: discord.Member):
        data = self.bot.cache.logging.get(member.guild.id)
        if not data or data["enabled"] is not True or not data.get("member_kick") or not data.get("channel_id"):
            return
        entry = [member async for member in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick)][0]
        if entry.target == member:
            channel = self.bot.get_channel(data["channel_id"])
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member} ({member.id}) has been kicked from {member.guild.name}.",
                color=discord.Color.red(),
            )
            embed.add_field(name="Responsible Moderator:", value=entry.user, inline=False)
            embed.add_field(name="Kick Reason:", value=entry.reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    @core.Cog.listener("on_guild_channel_create")
    async def logging_channel_create(self, channel: discord.abc.GuildChannel):
        thing = self.bot.cache.logging.get(channel.guild.id)
        if not thing:
            return
        if thing.get("enabled") is not True:
            return
        if not thing.get("channel_create"):
            return
        if not thing.get("channel_id"):
            return
        channel = self.bot.get_channel(thing["channel_id"])
        await channel.send(f"Channel has been created: {channel.mention}")

    @core.Cog.listener("on_guild_channel_delete")
    async def logging_channel_delete(self, channel: discord.abc.GuildChannel):
        thing = self.bot.cache.logging.get(channel.guild.id)
        if not thing:
            return
        if thing.get("enabled") is not True:
            return
        if not thing.get("channel_delete"):
            return
        if not thing.get("channel_id"):
            return
        channel = self.bot.get_channel(thing["channel_id"])
        await channel.send(f"Channel has been deleted: {channel.name}")

    @core.Cog.listener("on_guild_update")
    async def logging_guild(self, before: discord.Guild, after: discord.Guild):
        pass

    @tasks.loop(minutes=30)
    async def clear_cache(self):
        self.bot.command_cache.clear()

    @clear_cache.before_loop
    async def before_clear_cache(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BotLogs(bot))
