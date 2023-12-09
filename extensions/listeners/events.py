"""
[Alpine Bot]
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

import base64
import contextlib
import datetime as dt
import re
from io import BytesIO

import discord
from asyncgist import File
from discord.ext import commands, tasks

import core
from core import Bot, Context
from core.exceptions import Blacklisted, CommandDisabledChannel, CommandDisabledGuild, Maintenance
from utils import format_seconds

TOKEN_REGEX = r"([a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_\-]{27}|mfa\.[a-zA-Z0-9_\-]{84})"


edit_mapping = {
    "name": "Changed name",
    "category": "Moved channel category",
    "slowmode": "Set slowmode delay to",
    "topic": "Changed topic",
    "NSFW": "Set NSFW to",
}

toggle_mapping = {True: "On", False: "Off"}


class BotLogs(core.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = dt.datetime.now(dt.timezone.utc)
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
                description="Tokens found.",
                files=File(filename="tokens.txt", content="\n".join(tokens)),
                public=True,
            )
            embed = discord.Embed(
                description=(
                    f"Hey {message.author.name}, "
                    "I found Discord authentication tokens in your message. "
                    f"It was [uploaded to a Gist.]({gist.html_url})\n"
                ),
                color=discord.Color.red(),
                timestamp=dt.datetime.now(dt.timezone.utc),
            )
            embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)
            mentions = discord.AllowedMentions.all()
            if message.guild is None:
                return
            await message.reply(embed=embed, allowed_mentions=mentions, mention_author=True)

    @core.Cog.listener("on_message_delete")
    @core.Cog.listener("on_bulk_message_delete")
    async def logging_delete(self, message: discord.Message | list[discord.Message]):
        msg = message[0] if isinstance(message, list) else message
        if msg.guild is None:
            return
        settings = self.bot.database.get_guild(msg.guild.id)
        logging = settings.logging if settings else None
        if not logging or not logging.enabled or not logging.message_delete or not logging.webhook:
            return

        destination = logging.webhook

        if isinstance(message, discord.Message):
            context = await self.bot.get_context(message)
            if context.valid or message.author.bot or not isinstance(message.channel, discord.abc.GuildChannel):
                return
            embed = discord.Embed(
                title="Message Delete",
                timestamp=dt.datetime.now(dt.timezone.utc),
                description=f"Message from {message.author.mention} deleted in {message.channel.mention}",
                color=discord.Color.red(),
            )
            embed.set_footer(text="Deleted at")
            if message.content:
                embed.add_field(name="Deleted content", value=f">>> {message.content}")
            return await destination.send(embed=embed)

        assert isinstance(message, list)
        messages: list[discord.Message] = message

        list_of_messages = []
        for message in messages:
            timestamp = discord.utils.format_dt(message.created_at, "t")
            content = message.content[:90] or "*No content*"
            list_of_messages.append(f"[{timestamp}] {message.author}: {content}")
        if not list_of_messages:
            return
        embed = discord.Embed(
            title="Bulk Message Delete",
            timestamp=dt.datetime.now(dt.timezone.utc),
            color=discord.Color.red(),
        )
        embed.set_footer(text=f"{len(messages)} deleted")
        message_log = "\n\n----------\n\n".join(list_of_messages)
        if len(message_log) > 4000:
            message_file = discord.File(filename="messages.txt", fp=BytesIO(message_log.encode("utf-8")))
            return await destination.send(embed=embed, file=message_file)
        embed.description = "\n".join(list_of_messages)

    @core.Cog.listener("on_message_edit")
    async def logging_edit(self, before: discord.Message, after: discord.Message):
        context = await self.bot.get_context(after)
        guild_channel = discord.abc.GuildChannel
        if before.author.bot or context.valid or before.guild is None or after.guild is None:
            return
        elif not isinstance(before.channel, guild_channel) or not isinstance(after.channel, guild_channel):
            return

        settings = self.bot.database.get_guild(after.guild.id)
        logging = settings.logging if settings else None

        if not logging or not logging.enabled or not logging.message_edit or not logging.webhook:
            return
        elif before.content == after.content:
            return

        old_content = f"{before.content[:1017]}..." if len(before.content) > 1024 else before.content
        new_content = f"{after.content[:1017]}..." if len(after.content) > 1024 else after.content

        embed = discord.Embed(
            title="Message Edit",
            timestamp=dt.datetime.now(dt.timezone.utc),
            description=f"Message was edited by {before.author.mention} in {before.channel.mention}",
        )
        embed.add_field(name="Before", value=f">>> {old_content}", inline=False)
        embed.add_field(name="After", value=f">>> {new_content}", inline=False)
        embed.set_footer(text="Edited at")

        with contextlib.suppress(discord.HTTPException):
            return await logging.webhook.send(embed=embed)

    @core.Cog.listener("on_audit_log_entry_create")
    async def logging_ban_kick(self, entry: discord.AuditLogEntry):
        settings = self.bot.database.get_guild(entry.guild.id)
        logging = settings.logging if settings else None
        if not logging or not logging.enabled or not logging.webhook:
            return

        message = ""

        if entry.action == discord.AuditLogAction.ban:
            if not isinstance(entry.target, (discord.Object, discord.User)):
                return
            elif not logging.member_ban:
                return
            user = self.bot.get_user(entry.target.id)
            if not user or not entry.user:
                return
            message = (
                f"[**{discord.utils.format_dt(dt.datetime.now(dt.timezone.utc))}**] {user} (`{user.id}`) was banned:\n"
                f"> **Moderator:** {entry.user} (`{entry.user.id}`)\n"
                f"> **Reason:** {entry.reason}"
            )
        elif entry.action == discord.AuditLogAction.kick:
            if not isinstance(entry.target, (discord.Object, discord.User)):
                return
            elif not logging.member_leave:
                return
            user = self.bot.get_user(entry.target.id)
            if not user:
                return
            message = (
                f"[**{discord.utils.format_dt(dt.datetime.now(dt.timezone.utc))}**] {user} (`{user.id}`) was kicked:\n"
                f"> **Moderator:** {entry.user}\n"
                f"> **Reason:** {entry.reason or 'No reason provided.'}"
            )

        if not message:
            return
        with contextlib.suppress(discord.HTTPException):
            return await logging.webhook.send(message)

    @core.Cog.listener("on_guild_channel_update")
    async def logging_channel_create(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        settings = self.bot.database.get_guild(before.guild.id)
        logging = settings.logging if settings else None
        if not logging or not logging.enabled or not logging.channel_edit or not logging.webhook:
            return

        changed: list[
            tuple[
                str,
                str | discord.CategoryChannel | int | bool | None,
                str | discord.CategoryChannel | int | bool | None,
            ]
        ] = []
        if before.name != after.name:
            changed.append(("name", before.name, after.name))
        if before.category != after.category:
            changed.append(("category", before.category, after.category))
        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.slowmode_delay != after.slowmode_delay:
                changed.append(("slowmode", before.slowmode_delay, after.slowmode_delay))
            if before.topic != after.topic:
                changed.append(("topic", before.topic, after.topic))
            if before.nsfw != after.nsfw:
                changed.append(("NSFW", before.nsfw, after.nsfw))

        actions = []
        for action, pre, post in changed:
            if isinstance(post, bool):
                actions.append(f"{edit_mapping[action]} {toggle_mapping[post]}")
                continue
            if isinstance(post, str) and isinstance(pre, str):
                actions.append(f"{edit_mapping[action]} from **{pre[:500]}** to **{post[:500]}**")
                continue
            if isinstance(post, discord.CategoryChannel):
                actions.append(f"{edit_mapping[action]} from **{pre}** to **{post}**")
            if isinstance(post, int):
                actions.append(f"{edit_mapping[action]} {format_seconds(post, friendly=True)}")
                continue
        if not actions:
            return
        formatted = "\n".join(f"{num}. {action}" for num, action in enumerate(actions, 1))
        with contextlib.suppress(discord.HTTPException):
            return await logging.webhook.send(
                f"[**{discord.utils.format_dt(dt.datetime.now(dt.timezone.utc))}**] {after.mention} was edited:\n{formatted}"
            )

    @core.Cog.listener("on_guild_channel_delete")
    async def logging_channel_delete(self, channel: discord.abc.GuildChannel):
        settings = self.bot.database.get_guild(channel.guild.id)
        logging = settings.logging if settings else None
        if not logging or not logging.enabled or not logging.channel_delete or not logging.webhook:
            return

        return await logging.webhook.send(
            f"[**{discord.utils.format_dt(dt.datetime.now(dt.timezone.utc))}**] #{channel.name} was deleted"
        )

    @core.Cog.listener("on_guild_update")
    async def logging_guild(self, before: discord.Guild, after: discord.Guild):
        pass

    async def bot_check(self, ctx: Context) -> bool:
        blacklisted = ctx.database.get_blacklist(ctx.author.id)
        if blacklisted:
            raise Blacklisted(reason=blacklisted.reason)
        if not ctx.guild:
            raise commands.NoPrivateMessage
        guild_settings = ctx.database.get_guild(ctx.guild.id)
        if guild_settings:
            if ctx.command.qualified_name in guild_settings.disabled_commands:
                raise CommandDisabledGuild
            elif ctx.channel.id in guild_settings.disabled_channels:
                raise CommandDisabledChannel
        if ctx.bot.maintenance:
            raise Maintenance()
        return True

    @tasks.loop(minutes=30)
    async def clear_cache(self):
        self.bot.command_cache.clear()

    @clear_cache.before_loop
    async def before_clear_cache(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(BotLogs(bot))
