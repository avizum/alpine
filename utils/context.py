"""
Subclassed Command context
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

import asyncio
import discord
import datetime
import re

from .avimetry import AvimetryBot
from discord.ext import commands


class AvimetryContext(commands.Context):
    def __init__(self, bot: AvimetryBot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.tokens = []
        self.tokens.extend(self.bot.settings['bot_tokens'].values())
        self.tokens.extend(self.bot.settings['api_tokens'].values())
        self.tokens.extend(self.bot.settings['webhooks'].values())

    @property
    def cache(self):
        return self.bot.cache

    @property
    def pool(self):
        return self.bot.pool

    @property
    def clean_prefix(self):
        prefix = re.sub(
            f"<@!?{self.bot.user.id}>", f"@{self.me.display_name}", self.prefix
        )
        if prefix.endswith("  "):
            prefix = f"{prefix.strip()} "
        return prefix

    @property
    def content(self):
        return self.message.content

    @property
    async def get_prefix(self):
        get_prefix = await self.cache.get_guild_settings(self.guild.id)
        if get_prefix:
            prefix = get_prefix["prefixes"]
        if not prefix:
            return "`a.`"
        return f"`{'` | `'.join(prefix)}`"

    async def no_reply(self, *args, **kwargs):
        return await super().send(*args, **kwargs)

    async def post(self, content, syntax=None, gist: bool = False):
        if gist:
            raise NotImplementedError("Will add later")
        if syntax is None:
            syntax = "python"
        link = await self.bot.myst.post(content, syntax=syntax)
        embed = discord.Embed(
            description=f"Output for {self.command.qualified_name}: [Here]({link})"
        )
        await self.send(embed=embed)

    async def determine_color(self):
        base = self.author.color
        data = self.cache.users.get(self.author.id)
        try:
            color = data.get('color')
            if not color:
                color = base
        except AttributeError:
            color = self.author.color
        if color == discord.Color(0):
            if await self.bot.is_owner(self.author):
                color = discord.Color(0x01b9c0)
            else:
                color = discord.Color(0x2F3136)
        return color

    async def send(self, content: str = None, embed: discord.Embed = None, no_reply: bool = False, **kwargs):
        if content:
            content = str(content)
            for token in self.tokens:
                content = content.replace(token, "[config omitted]")
        if embed:
            if not embed.footer:
                embed.set_footer(
                    text=f"Requested by {self.author}",
                    icon_url=str(self.author.avatar_url)
                )
                embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            if not embed.color:
                embed.color = await self.determine_color()
        if self.message.id in self.bot.command_cache and not kwargs.get('file') and self.message.edited_at:
            message = self.bot.command_cache[self.message.id]
            await message.edit(content=content, embed=embed, mention_author=False, file=None, files=None)
        else:
            try:
                if no_reply:
                    message = await super().send(content=content, embed=embed, mention_author=False, **kwargs)
                else:
                    message = await self.reply(content=content, embed=embed, mention_author=False, **kwargs)
            except discord.HTTPException:
                message = await super().send(content=content, embed=embed, mention_author=False, **kwargs)
        self.bot.command_cache[self.message.id] = message
        return message

    async def codeblock(self, content: str, language: str = 'py', **kwargs):
        content = f"```{language}\n{content}\n```"
        await self.send(content=content, **kwargs)

    async def confirm(
        self, message=None, embed: discord.Embed = None, confirm_message=None, *,
        timeout=60, delete_after=True, raw=False
    ):
        emojis = self.bot.emoji_dictionary
        yes_no = [emojis['green_tick'], emojis['red_tick']]
        check_message = confirm_message or f"React with {yes_no[0]} to accept, or {yes_no[1]} to deny."
        if raw is True:
            send = await self.no_reply(content=message, embed=embed)
        elif message:
            message = f"{message}\n\n{check_message}"
            send = await self.send(message)
        elif embed:
            embed.description = f"{embed.description}\n\n{check_message}"
            send = await self.send(embed=embed)
        for emoji in yes_no:
            await send.add_reaction(emoji)

        def check(reaction, user):
            return str(reaction.emoji) in yes_no and user == self.author and reaction.message.id == send.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = False
        else:
            if str(reaction.emoji) == yes_no[0]:
                confirm = True
            if str(reaction.emoji) == yes_no[1]:
                confirm = False
        if delete_after:
            await send.delete()
        return confirm

    async def prompt(
        self, message=None, embed: discord.Embed = None, *,
        timeout=60, delete_after=True, raw=False
    ):
        if raw is True:
            send = await self.no_reply(content=message, embed=embed)
        elif message:
            message = f"{message}"
            send = await self.send(message)
        elif embed:
            embed.description = f"{embed.description}\n\n{message or ''}"
            send = await self.send(embed=embed)

        def check(message: discord.Message):
            return self.author == message.author and self.channel == message.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = False
            pass
        else:
            return msg.content
        if delete_after:
            await send.delete()
        return confirm

    async def can_delete(self, *args, **kwargs):
        emoji = self.bot.emoji_dictionary["red_tick"]
        message = await self.send(*args, **kwargs)
        await message.add_reaction(emoji)

        def check(reaction, user):
            return str(reaction.emoji) in emoji and user == self.author and reaction.message.id == message.id

        reaction, user = await self.bot.wait_for("reaction_add", check=check)
        if str(reaction.emoji) == emoji:
            await message.delete()


def setup(bot):
    bot.context = AvimetryContext


def teardown(bot):
    bot.context = commands.Context
