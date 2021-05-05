import re
import discord
from discord.ext import commands
from utils.context import AvimetryContext


time_regex = re.compile(r"(?:(\d{1,5})\s?(h|s|m|d))+?")
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
    "days": 86400
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
                    f"{value} is an invalid time-key! h/m/s/d are valid!")
            except ValueError:
                raise commands.BadArgument(f"{key} is not a number!")
        return time


class Reason(commands.Converter):
    async def convert(self, ctx, argument):
        reason = f"{ctx.author}: {argument}"
        if argument is None:
            reason = f"{ctx.author}: No reason was provided."

        if len(reason) > 512:
            raise commands.BadArgument(f"Reason is too long ({len(reason)}/512")
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
            await ctx.cache.cache_new_guild(ctx.guild.id)
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

        return argument


class CogConverter(commands.Converter):
    async def convert(self, ctx: AvimetryContext, argument):
        exts = []
        if argument in ["~", "*", "a", "all"]:
            exts.extend(ctx.bot.extensions)
        else:
            exts.append(f"cogs.{argument}")
        jsk = "cogs.jishaku"
        if jsk in exts:
            exts.remove("cogs.jishaku")
        return exts
