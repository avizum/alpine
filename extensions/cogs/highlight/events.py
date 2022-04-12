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

        for user_id, data in self.bot.cache.highlights.items():
            if user_id == message.author.id:
                continue

            reg = "|".join(f"({entry['phrase']})" for entry in data)

            match = re.search(reg, message.content, re.IGNORECASE)
            if not match:
                continue

            groups = match.groups()
            try:
                phrase = discord.utils.find(lambda e: e["phrase"] in groups, data)["phrase"]
            except KeyError:
                phrase = None
            if not phrase:
                continue

            if history is None:
                def check(msg: discord.Message):
                    return msg.author.id == user_id and msg.channel == message.channel

                try:
                    await self.bot.wait_for_message(check=check, timeout=8)
                except asyncio.TimeoutError:
                    messages = []
                    async for msg in message.channel.history(limit=9, around=message):
                        if msg.id == message.id:
                            messages.append(
                                f"[**[{format_dt(msg.created_at, 't')}] {msg.author}: {msg.content}**]({msg.jump_url})"
                            )
                        else:
                            messages.append(
                                f"[{format_dt(msg.created_at, 't')}] {msg.author}: {msg.content}"
                            )
                    messages.reverse()
                    embed = discord.Embed(
                        title=f"Highlight trigger: {phrase}",
                        description=(
                            f"In the server {message.guild.name}, you were highlighted"
                            f" by {message.author.mention} ({message.author.id})."
                        ),
                        color=0xF2D413,
                    )
                    embed.add_field(
                        name="Messages",
                        value="\n".join(messages),
                    )
                    user = (
                        message.guild.get_member(user_id)
                        or self.bot.get_user(user_id)
                        or await self.bot.fetch_user(user_id)
                    )
                    if not user:
                        continue
                    try:
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        continue
                else:
                    continue
