"""
[Avimetry Bot]
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

import re

from discord.ext import commands

from core import Context

PREFIX_CHAR_LIMIT = 35
MAX_PREFIX_AMOUNT = 20


class Prefix(commands.Converter, str):
    @classmethod
    async def convert(cls, ctx: Context, argument) -> str:
        user_mention = re.findall(r"<@(!?)([0-9]*)>", argument)
        role_mention = re.findall(r"<@&(\d+)>", argument)
        channel_mention = re.findall(r"<#(\d+)>", argument)
        guild_cache = await ctx.cache.get_guild_settings(ctx.guild.id)
        if not guild_cache:
            guild_cache = await ctx.cache.cache_new_guild(ctx.guild.id)
        guild_prefix = guild_cache["prefixes"]
        if user_mention:
            raise commands.BadArgument("You can not add a mention as a prefix.")
        elif role_mention:
            raise commands.BadArgument("You can not add a role mention as a prefix.")
        elif channel_mention:
            raise commands.BadArgument("You can not add a channel mention as a prefix.")
        elif len(argument) > PREFIX_CHAR_LIMIT:
            raise commands.BadArgument(f"That prefix is too long ({len(argument)}/{PREFIX_CHAR_LIMIT})")
        elif len(guild_prefix) > MAX_PREFIX_AMOUNT:
            raise commands.BadArgument(f"You already the max amount of prefixes {MAX_PREFIX_AMOUNT} prefixes")
        elif argument in guild_prefix:
            raise commands.BadArgument("That is already a prefix for this server.")

        return argument.lower()


class GetCommand(commands.Converter):
    async def convert(self, ctx: Context, argument: str):
        command = ctx.bot.get_command(argument)
        if not command:
            raise commands.BadArgument(f"{argument} is not a command.")
        return command
