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

import re
from typing import Union

import discord
from discord.ext import commands

from core import Context, flag
from utils import ModReason


class ModActionFlag(commands.FlagConverter):
    reason: ModReason = flag(default=None, description="Reason that will show up in the audit log.")
    dm: bool = flag(default=False, description="Whether to DM the user.")

class BanFlag(ModActionFlag):
    delete_days: int = flag(default=0, description="How many days of messages to delete.")

time_regex = re.compile(r"(?:(\d{1,5})\s?(h|s|m|d|w|y))+?")
time_dict = {
    "h": 3600,
    "hours": 3600,
    "hour": 3600,
    "s": 1,
    "sec": 1,
    "secs": 1,
    "seconds": 1,
    "m": 60,
    "mins": 60,
    "minutes": 60,
    "min": 60,
    "d": 86400,
    "day": 86400,
    "days": 86400,
    "w": 604800,
    "week": 604800,
    "weeks": 604800,
    "y": 31557600,
    "year": 31557600,
    "years": 31557600,
}

class TimeConverter(commands.Converter):
    async def convert(self, ctx: Context, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for key, value in matches:
            try:
                time += time_dict[value] * float(key)
            except KeyError:
                raise commands.BadArgument(f"{value} is an invalid time-key!")
            except ValueError:
                raise commands.BadArgument(f"{key} is not a number!")
        if time < 0:
            raise commands.BadArgument("Time can not be under 1 second")
        return time

class PurgeAmount(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            number = int(argument)
        except Exception as e:
            raise commands.BadArgument(
                f"{argument} is not a number. Please give a number."
            ) from e
        if number < 1 or number > 1000:
            raise commands.BadArgument(
                "Number must be greater than 0 and less than 1000"
            )
        return number

class TargetMember(commands.Converter[discord.Member]):
    async def convert(
        self, ctx: Context, argument: discord.Member
    ) -> discord.Member:
        try:
            member = await commands.MemberConverter().convert(ctx, argument)
        except Exception:
            member = await commands.UserConverter().convert(ctx, argument)
            return member
        action = ctx.invoked_with

        if member == ctx.guild.owner:
            raise commands.BadArgument(f"I can not {action} the server owner.")

        if member == ctx.message.author:
            raise commands.BadArgument(
                f"You can not {action} yourself, That would be stupid."
            )

        if ctx.me.top_role < member.top_role:
            raise commands.BadArgument(
                f"I can not {action} {member} because their top role is higher than my top role."
            )

        if ctx.me.top_role == member.top_role:
            raise commands.BadArgument(
                f"I can't {action} {member} because they have the same top role as me."
            )

        if member == ctx.me:
            raise commands.BadArgument(f"I can not {action} myself. Nice try.")

        if ctx.author.top_role < member.top_role:
            raise commands.BadArgument(
                f"You can't {action} {member} because their role is is higher than your role."
            )

        if ctx.author.top_role == member.top_role:
            raise commands.BadArgument(
                f"You can't {action} {member} because they have the same top role as you."
            )

        return member

class FindBan(commands.Converter[discord.Member]):
    async def convert(
        self, ctx: Context, argument: str
    ) -> Union[discord.Member, discord.User]:
        try:
            user = await commands.UserConverter().convert(ctx, argument)
            try:
                await ctx.guild.fetch_ban(user)
            except discord.NotFound:
                raise commands.BadArgument("That user isn't banned.")
            return user
        except commands.UserNotFound:
            bans = await ctx.guild.bans()
            for ban in bans:
                if str(ban[1]).startswith(argument):
                    return ban[1]

        raise commands.BadArgument("That user isn't banned")
