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
import contextlib
import re
import toml

from discord.ext import commands


with open("config.toml") as f:
    settings = toml.loads(f.read())
    bot_tokens = (settings["bot_tokens"].values())
    api_tokens = (settings["api_tokens"].values())
    tokens = list(bot_tokens)
    tokens.extend(api_tokens)


class AvimetryContext(commands.Context):

    @property
    def cache(self):
        return self.bot.cache

    @property
    def clean_prefix(self):
        prefix = re.sub(
            f"<@!?{self.bot.user.id}>", f"@{self.me.display_name}", self.prefix
        )
        if prefix.endswith("  "):
            prefix = f"{prefix.strip()} "
        return prefix

    @property
    async def get_prefix(self):
        get_prefix = await self.cache.get_guild_settings(self.guild.id)
        if get_prefix:
            prefix = get_prefix["prefixes"]
        if not prefix:
            return "`a.`"
        return f"`{'` | `'.join(prefix)}`"

    async def send_raw(self, *args, **kwargs):
        return await super().send(*args, **kwargs)

    async def post(self, content, syntax=None):
        if syntax is None:
            syntax = "python"
        link = await self.bot.myst.post(content, syntax=syntax)
        embed = discord.Embed(
            description=f"Output for {self.invoked_with}: [Here]({link})"
        )
        await self.send(embed=embed)

    async def send(self, content=None, embed: discord.Embed = None, **kwargs):
        content = str(content) if content is not None else None
        if not self.command:
            self.command = self.bot.get_command("_")
        if content and not embed:
            if "jishaku" in self.command.qualified_name:
                message = await self.reply(content=content, embed=embed, **kwargs)
                return message
            embed = discord.Embed(description=content)
            content = None
        if embed:
            if not embed.footer:
                embed.set_footer(
                    text=f"{self.author}",
                    icon_url=str(self.author.avatar_url)
                )
                embed.timestamp = datetime.datetime.utcnow()
            if not embed.color:
                color = self.author.color
                if self.author.color in [
                    discord.Color(0),
                    discord.Color(0xFFFFFF),
                ]:
                    color = discord.Color(0x2F3136)
                embed.color = color
        if self.message.id in self.bot.command_cache and self.message.edited_at:
            edited_message = self.bot.command_cache[self.message.id]
            try:
                await edited_message.clear_reactions()
            except Exception:
                pass
            try:
                await edited_message.edit(content=content, embed=embed, **kwargs)
                return edited_message
            except Exception:
                pass
        try:
            message = await self.reply(content=content, embed=embed, **kwargs)
            return message
        except Exception:
            try:
                message = await self.send_raw(content=content, embed=embed, **kwargs)
                return message
            except Exception:
                message = await self.post(content=content)
                return message
        finally:
            with contextlib.suppress(Exception):
                self.bot.command_cache[self.message.id] = message

    async def confirm(
        self, message=None, embed: discord.Embed = None, confirm_message=None, *,
        timeout=60, delete_after=True, raw=False
    ):
        emojis = self.bot.emoji_dictionary
        yes_no = [emojis['green_tick'], emojis['red_tick']]
        check_message = confirm_message or f"React with {yes_no[0]} to accept, or {yes_no[1]} to deny."
        if raw is True:
            send = await self.send_raw(content=message, embed=embed)
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
            pass
        else:
            if str(reaction.emoji) == yes_no[0]:
                confirm = True
            if str(reaction.emoji) == yes_no[1]:
                confirm = False
        if delete_after:
            await send.delete()
        return confirm

    async def delete(self, *args, **kwargs):
        emoji = self.bot.emoji_dictionary["red_tick"]
        message = await self.send(*args, **kwargs)
        await message.add_reaction(emoji)

        def check(reaction, user):
            return str(reaction.emoji) in emoji and user == self.author and reaction.message.id == message.id

        reaction, user = await self.bot.wait_for("reaction_add", check=check)
        if str(reaction.emoji) == emoji:
            await message.delete()


def setup(avi):
    avi.context = AvimetryContext


def teardown(avi):
    avi.context = commands.Context
