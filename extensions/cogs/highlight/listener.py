"""
[Alpine Bot]
Copyright (C) 2021 - 2024 avizum

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
import re

import discord
from discord.utils import format_dt

import core
from core import Bot


class HighlightListener(core.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @core.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        if not message.content:
            return

        history = None

        highlight_list = []
        for user_id, highlight in self.bot.database._highlights.items():
            if user_id == message.author.id:
                continue

            if highlight.blocked and message.author.id in highlight.blocked or message.channel.id in highlight.blocked:
                continue

            for word in highlight.triggers:
                highlight_list.append(word)
            reg = "|".join(rf"\b({h})\b" for h in highlight_list)

            match = re.search(reg, message.content.lower(), flags=re.IGNORECASE)
            if not match:
                continue

            trigger = discord.utils.find(lambda t: t in match.groups(), highlight.triggers)  # type: ignore
            if not trigger:
                continue

            if history is None:

                def check(msg: discord.Message):
                    return msg.author.id == user_id and msg.channel == message.channel

                try:
                    await self.bot.wait_for_message(check=check, timeout=25)
                except asyncio.TimeoutError:
                    messages = []
                    async for msg in message.channel.history(limit=9, around=message):
                        timestamp = format_dt(msg.created_at, "t")
                        author = msg.author
                        content = msg.content[:90] or "*No message content*"
                        if msg.id == message.id:
                            content = content.replace(trigger, f"*__{trigger}__*")
                            messages.append(f"[**[{timestamp}] {author}: {content}**]({msg.jump_url})")
                        else:
                            messages.append(f"[{timestamp}] {author}: {content}")
                    messages.reverse()
                    embed = discord.Embed(
                        title=f"Highlight trigger: {trigger}",
                        description=(
                            f"In the server {message.guild.name}, you were highlighted"
                            f" by {message.author.mention} ({message.author.id})."
                        ),
                        color=0x30C5FF,
                        timestamp=message.created_at,
                    )
                    embed.add_field(
                        name="Messages",
                        value="\n".join(messages),
                    )
                    embed.set_footer(text="Triggered at")
                    user = (
                        message.guild.get_member(user_id) or self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    )
                    if not user:
                        continue
                    if user and user not in message.guild.members:
                        continue
                    try:
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        continue
                else:
                    continue
