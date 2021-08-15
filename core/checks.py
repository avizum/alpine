import inspect
import functools
import discord

from discord.ext import commands
from .core import AvimetryCommand


def check(predicate, user_permissions=None, bot_permissions=None):
    def decorator(func):
        if user_permissions:
            func.user_permissions = user_permissions
        if bot_permissions:
            func.bot_permissions = bot_permissions
        if isinstance(func, AvimetryCommand):
            func.checks.append(predicate)
        else:
            if not hasattr(func, '__commands_checks__'):
                func.__commands_checks__ = []

            func.__commands_checks__.append(predicate)

        return func

    if inspect.iscoroutinefunction(predicate):
        decorator.predicate = predicate
    else:
        @functools.wraps(predicate)
        async def wrapper(ctx):
            return predicate(ctx)
        decorator.predicate = wrapper
    return decorator


def has_permissions(**perms):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    async def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if await ctx.bot.is_owner(ctx.author):
            return True
        if not missing:
            return True

        raise commands.MissingPermissions(missing)
    return check(predicate, user_permissions=perms)


def bot_has_permissions(**perms):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    async def predicate(ctx):
        guild = ctx.guild
        me = guild.me if guild is not None else ctx.bot.user
        permissions = ctx.channel.permissions_for(me)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise commands.BotMissingPermissions(missing)

    return check(predicate, bot_permissions=perms)


def is_owner():
    async def predicate(ctx):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner('You do not own this bot.')
        return True

    return check(predicate, user_permissions=['bot_owner'])
