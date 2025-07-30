"""
[Alpine Bot]
Copyright (C) 2021 - 2025 avizum

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
import contextlib
import re
from typing import TYPE_CHECKING

import discord

import core
from utils import timestamp

if TYPE_CHECKING:
    from core import Bot
    from utils import HighlightsData


class HighlightListener(core.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.raw_highlights: dict[int, HighlightsData] = self.bot.database._highlights

    def is_valid(self, message: discord.Message) -> bool:
        if message.guild is None or message.author.bot or message.webhook_id or message.content is None:
            return False
        return True

    def can_see_channel(self, member: discord.Member, channel: discord.abc.MessageableChannel):
        return channel.permissions_for(member).read_messages

    async def notify_user(self, message: discord.Message, member: discord.Member, trigger: str):
        assert message.guild is not None

        if not self.can_see_channel(member, message.channel):
            return

        embed = discord.Embed(
            title=f"Highlight trigger: {trigger}",
            description=(
                f"In the server {message.guild.name}, you were highlighted"
                f" by {message.author.mention} ({message.author.id}).\n{message.jump_url}"
            ),
            color=0x30C5FF,
            timestamp=message.created_at,
        )

        messages: list[str] = []
        contents: list[str] = []
        async for msg in message.channel.history(limit=9, around=message, oldest_first=True):
            time = format(timestamp(msg.created_at), "t")
            author = msg.author
            content = msg.content

            prefix = f"[{time}]"
            if msg.id == message.id:
                prefix = f"**[{time}]**"
            fmt_content = f"{prefix} @{author}: {content}"
            joined_len = len("\n".join(contents))

            if (joined_len + len(fmt_content)) <= 1024:

                contents.append(fmt_content)
            elif len(fmt_content) >= 1024:

                if (joined_len + len(fmt_content)) >= 1024:

                    messages.append("\n".join(contents))
                    contents.clear()

                contents.append(f"{fmt_content[:1021]}...")
            else:

                messages.append("\n".join(contents))
                contents.clear()
                contents.append(fmt_content)

        messages.append("\n".join(contents))

        for message_content in messages:
            embed.add_field(name="\u200b", value=message_content, inline=False)

        embed.set_field_at(0, name="Messages", value=embed.fields[0].value)
        embed.set_footer(text="Triggered at")
        with contextlib.suppress(discord.Forbidden):
            await member.send(embed=embed)

    @core.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.is_valid(message):
            return

        assert message.guild is not None

        highlight_list = []
        for user_id, highlight in self.bot.database._highlights.items():
            if user_id == message.author.id:
                continue

            if highlight.blocked and message.author.id in highlight.blocked or message.channel.id in highlight.blocked:
                continue

            for word in highlight.triggers:
                highlight_list.append(word)

            reg = "|".join(rf"\b({re.escape(h)})\b" for h in highlight_list)

            match = re.search(reg, message.content.lower(), flags=re.IGNORECASE)
            if not match:
                continue

            trigger = discord.utils.find(lambda t: t in match.groups(), highlight.triggers)  # type: ignore
            if not trigger:
                continue

            def check(msg: discord.Message):
                return msg.author.id == user_id and msg.channel == message.channel

            try:
                await self.bot.wait_for("message", check=check, timeout=25)
            except asyncio.TimeoutError:
                member = message.guild.get_member(user_id)
                if not member:
                    return

                await self.notify_user(message, member, trigger)
