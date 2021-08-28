"""
Cog to listen to events for logging
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
import datetime
import asyncio
import base64
import re
import core

from discord.ext import tasks
from utils import AvimetryBot, Gist

TOKEN_REGEX = r'[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}'


class BotLogs(core.Cog):
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.clear_cache.start()
        self.gist = Gist(self.bot, self.bot.session)

    @core.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user or message.author.id == 80528701850124288:
            return
        tokens = re.findall(TOKEN_REGEX, message.content)
        if tokens:
            gist = await self.gist.post(
                filename="tokens.txt",
                description="Tokens found.",
                content="\n".join(tokens),
                public=True
            )

            split_token = tokens[0].split(".")
            try:
                user_bytes = split_token[0].encode()
                user_id_decoded = base64.b64decode(user_bytes)
                uid = user_id_decoded.decode("ascii")
            except Exception:
                uid = 0
            embed = discord.Embed(
                description=(
                    f"Hey {message.author.name},\n"
                    f"It appears that you posted a Discord token here. I uploaded it [here.]({gist})\n"
                    f"You can get a new token [here.](https://discord.com/developers/applications/{uid}/bot)"
                ),
                color=discord.Color.red(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)
            mentions = discord.AllowedMentions.all()
            try:
                if message.guild is not None and message.guild.id == 336642139381301249:
                    return
                await message.reply(embed=embed, allowed_mentions=mentions, mention_author=True)
            except discord.Forbidden:
                return

    @core.Cog.listener("on_message_delete")
    async def logging_delete(self, message: discord.Message):
        context = await self.bot.get_context(message)
        if context.valid:
            return
        if not message.guild:
            return
        data = self.bot.cache.logging.get(message.guild.id)
        if not data or data["enabled"] is not True or not data["message_delete"] or not data["channel_id"]:
            return
        if message.author == self.bot.user or message.author.bot:
            return
        embed = discord.Embed(
            title="Message Delete", timestamp=datetime.datetime.now(datetime.timezone.utc),
            description=f"Message was deleted by {message.author.mention} in {message.channel.mention}"
        )
        embed.set_footer(text="Deleted at")
        if message.content:
            embed.add_field(name="Deleted content", value=f">>> {message.content}")
        if not message.content:
            return
        channel_id = data["channel_id"]
        channel = discord.utils.get(message.guild.channels, id=channel_id)
        await channel.send(embed=embed)

    @core.Cog.listener("on_message_edit")
    async def logging_edit(self, before: discord.Message, after: discord.Message):
        context = await self.bot.get_context(after)
        if context.valid:
            return
        if before.guild is None and after.guild is None:
            return
        data = self.bot.cache.logging.get(before.guild.id)
        if not data or data["enabled"] is not True or not data["message_edit"] or not data["channel_id"]:
            return
        if before.author == self.bot.user or before.author.bot:
            return
        if before.content == after.content:
            return
        bef_con = f"{str(before.content[:1017])}..." if len(before.content) > 1024 else before.content
        aft_con = f"{str(after.content[:1017])}..." if len(after.content) > 1024 else after.content
        embed = discord.Embed(
            title="Message Edit", timestamp=datetime.datetime.now(datetime.timezone.utc),
            description=f"Message was edited by {before.author.mention} in {before.channel.mention}"
        )
        embed.add_field(name="Message Before", value=f">>> {bef_con}", inline=False)
        embed.add_field(name="Message After", value=f">>> {aft_con}", inline=False)
        embed.set_footer(text="Edited at")
        channel_id = data["channel_id"]
        channel = discord.utils.get(before.guild.channels, id=channel_id)
        await channel.send(embed=embed)

    @core.Cog.listener("on_member_ban")
    async def logging_ban(self, guild: discord.Guild, user: discord.User):
        data = self.bot.cache.logging.get(guild.id)
        if not data or data["enabled"] is not True or not data["member_ban"] or not data["channel_id"]:
            return
        await asyncio.sleep(2)
        entry = (await guild.audit_logs(limit=1, action=discord.AuditLogAction.ban).flatten())[0]
        if entry.target == user:
            channel = self.bot.get_channel(data["channel_id"])
            embed = discord.Embed(
                title="Member Banned",
                description=f"{user} ({user.id}) has been banned from {guild.name}.",
                color=discord.Color.red()
            )
            embed.add_field(name="Responsible Moderator:", value=entry.user, inline=False)
            embed.add_field(name="Ban Reason:", value=entry.reason, inline=False)
            embed.set_thumbnail(url=user.display_avatar.url)
            await channel.send(embed=embed)

    @core.Cog.listener("on_member_remove")
    async def loggging_kick(self, member: discord.Member):
        data = self.bot.cache.logging.get(member.guild.id)
        if not data or data["enabled"] is not True or not data["member_kick"] or not data["channel_id"]:
            return
        entry = (await member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick).flatten())[0]
        if entry.target == member:
            channel = self.bot.get_channel(data["channel_id"])
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member} ({member.id}) has been kicked from {member.guild.name}.",
                color=discord.Color.red()
            )
            embed.add_field(name="Responsible Moderator:", value=entry.user, inline=False)
            embed.add_field(name="Kick Reason:", value=entry.reason, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    @core.Cog.listener("on_guild_channel_create")
    async def logging_channel_one(self, channel: discord.abc.GuildChannel):
        thing = self.bot.cache.logging.get(channel.guild.id)
        if not thing:
            return
        if thing["enabled"] is not True:
            return
        if not thing["channel"]:
            return
        if not thing["channel_id"]:
            return
        channel = self.bot.get_channel(thing["channel_id"])
        await channel.send(f"Channel has been created: {channel.mention}")

    @core.Cog.listener("on_guild_channel_delete")
    async def logging_channel_two(self, channel: discord.abc.GuildChannel):
        thing = self.bot.cache.logging.get(channel.guild.id)
        if not thing:
            return
        if thing["enabled"] is not True:
            return
        if not thing["channel"]:
            return
        if not thing["channel_id"]:
            return
        channel = self.bot.get_channel(thing["channel_id"])
        await channel.send(f"Channel has been deleted: {channel.name}")

    @core.Cog.listener("on_guild_channel_edit")
    async def logging_channel_three(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        thing = self.bot.cache.logging.get(before.guild.id)
        if not thing:
            return
        if thing["enabled"] is not True:
            return
        if not thing["channel"]:
            return
        if not thing["channel_id"]:
            return

    @core.Cog.listener("on_guild_update")
    async def logging_guild(self, before: discord.Guild, after: discord.Guild):
        pass

    @tasks.loop(minutes=30)
    async def clear_cache(self):
        self.bot.command_cache.clear()

    @clear_cache.before_loop
    async def before_clear_cache(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(BotLogs(bot))
