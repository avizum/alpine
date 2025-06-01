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

import re

from discord.ext import commands

from core import Command, Context

PREFIX_CHAR_LIMIT = 35
MAX_PREFIX_AMOUNT = 20

MENTION_REGEX: re.Pattern = re.compile(r"<(@!?|#|&)([\d]*)>")


class Prefix(commands.Converter, str):
    @classmethod
    async def convert(cls, ctx: Context, argument) -> str:
        settings = await ctx.database.get_or_fetch_guild(ctx.guild.id)
        prefixes = settings.prefixes

        if MENTION_REGEX.match(argument):
            raise commands.BadArgument("You can not add a mention as a prefix.")
        if len(argument) > PREFIX_CHAR_LIMIT:
            raise commands.BadArgument(f"That prefix is too long ({len(argument)}/{PREFIX_CHAR_LIMIT})")
        if len(prefixes) > MAX_PREFIX_AMOUNT:
            raise commands.BadArgument(f"You already the max amount of prefixes {MAX_PREFIX_AMOUNT} prefixes")
        if argument in prefixes:
            raise commands.BadArgument("That is already a prefix for this server.")

        return argument.lower()


class GetCommand(commands.Converter, Command):
    @classmethod
    async def convert(cls, ctx: Context, argument: str):
        command = ctx.bot.get_command(argument)
        if not command:
            raise commands.BadArgument(f"{argument} is not a command.")
        if command.cog_name and command.cog_name in ("Bot Info", "HelpCommand", "Settings"):
            raise commands.BadArgument("You can not disable this command.")
        return command
