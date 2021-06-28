"""
Custom converters for the bot.
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

import re
import discord

from discord.ext import commands
from utils import AvimetryContext
from twemoji_parser import emoji_to_url as urlify_emoji


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
    "years": 31557600
}


class TimeConverter(commands.Converter):
    async def convert(self, ctx: AvimetryContext, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for key, value in matches:
            try:
                time += time_dict[value]*float(key)
            except KeyError:
                raise commands.BadArgument(
                    f"{value} is an invalid time-key!")
            except ValueError:
                raise commands.BadArgument(f"{key} is not a number!")
        if time < 0:
            raise commands.BadArgument("Time can not be under 1 second")
        return time


class ModReason(commands.Converter):
    async def convert(self, ctx, argument):
        reason = f"{ctx.author}: {argument}"
        if argument is None:
            reason = f"{ctx.author}: No reason was provided."

        if len(reason) > 512:
            raise commands.BadArgument(f"Reason is too long ({len(reason)}/512)")
        return reason


class TargetMemberAction(commands.Converter):
    async def convert(self, ctx: AvimetryContext, argument: discord.Member):
        try:
            member = await commands.MemberConverter().convert(ctx, argument)
        except Exception:
            member = await commands.UserConverter().convert(ctx, argument)
            return member
        action = ctx.invoked_with

        if member == ctx.guild.owner:
            raise commands.BadArgument(
                f"I can not {action} the server owner."
            )

        if member == ctx.message.author:
            raise commands.BadArgument(f"You can not {action} yourself, That would be stupid.")

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


class FindBan(commands.Converter):
    async def convert(self, ctx: AvimetryContext, argument: str):
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


PREFIX_CHAR_LIMIT = 20
MAX_PREFIX_AMOUNT = 15


class Prefix(commands.Converter):
    async def convert(self, ctx: AvimetryContext, argument):
        user_mention = re.findall(r"<@(!?)([0-9]*)>", argument)
        role_mention = re.findall(r"<@&(\d+)>", argument)
        channel_mention = re.findall(r"<#(\d+)>", argument)
        guild_cache = await ctx.cache.get_guild_settings(ctx.guild.id)
        if not guild_cache:
            g = await ctx.cache.cache_new_guild(ctx.guild.id)
            guild_prefix = g["prefixes"]
        else:
            guild_prefix = guild_cache["prefixes"]
        if user_mention:
            raise commands.BadArgument("You can not add a mention as a prefix.")
        if role_mention:
            raise commands.BadArgument("You can not add a role mention as a prefix.")
        if channel_mention:
            raise commands.BadArgument("You can not add a channel mention as a prefix.")
        if len(argument) > PREFIX_CHAR_LIMIT:
            raise commands.BadArgument(f"That prefix is too long ({len(argument)}/{PREFIX_CHAR_LIMIT})")
        if len(guild_prefix) > MAX_PREFIX_AMOUNT:
            raise commands.BadArgument(f"You already the max amount of prefixes {MAX_PREFIX_AMOUNT} prefixes")
        if argument in guild_prefix:
            raise commands.BadArgument("That is already a prefix for this server.")

        return argument.lower()


class CogConverter(commands.Converter):
    async def convert(self, ctx: AvimetryContext, argument):
        exts = []
        if argument in ["~", "*", "a", "all"]:
            exts.extend(ctx.bot.extensions)
        else:
            exts.append(argument)
        jsk = "cogs.jishaku"
        if jsk in exts:
            exts.remove("cogs.jishaku")
        return exts


regex_url = re.compile(
    r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+"
    r"[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
)
emoji_regex = r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>"


class GetAvatar(commands.Converter):
    async def convert(self, ctx: AvimetryContext, argument: str = None):
        try:
            member_converter = commands.MemberConverter()
            member = await member_converter.convert(ctx, argument)
            image = member.avatar_url_as(format="png", static_format="png", size=1024)
            return str(image)
        except Exception:
            try:
                url = await urlify_emoji(argument)
                if re.match(regex_url, url):
                    image = str(url)
                    return image
                if re.match(regex_url, argument):
                    image = argument
                    return image
                if re.match(emoji_regex, argument):
                    emoji_converter = commands.EmojiConverter()
                    emoji = emoji_converter.convert(ctx, argument)
                    image = emoji.url_as(format="png", static_format="png", size=1024)
                    return image
            except Exception:
                return None
        raise commands.MemberNotFound(argument)
