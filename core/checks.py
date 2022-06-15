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

from __future__ import annotations

import inspect
import functools
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from .core import Command
from .exceptions import NotGuildOwner

if TYPE_CHECKING:
    from .context import Context

def check(predicate: any, member_permissions: bool = None, bot_permissions: bool = None):
    def decorator(func):
        if member_permissions:
            func.member_permissions = member_permissions
        if bot_permissions:
            func.bot_permissions = bot_permissions
        if isinstance(func, Command):
            func.checks.append(predicate)
        else:
            if not hasattr(func, "__commands_checks__"):
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


def has_permissions(**perms: bool):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    async def predicate(ctx: Context):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if await ctx.bot.is_owner(ctx.author):
            return True
        if not missing:
            return True

        raise commands.MissingPermissions(missing)

    return check(predicate, member_permissions=perms)


def bot_has_permissions(**perms: bool):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    async def predicate(ctx: Context):
        guild = ctx.guild
        me = guild.me if guild is not None else ctx.bot.user
        permissions = ctx.channel.permissions_for(me)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise commands.BotMissingPermissions(missing)

    return check(predicate, bot_permissions=perms)


def cooldown(rate: int, per: float, type=commands.BucketType.default):
    def decorator(func):
        if isinstance(func, Command):
            func._buckets = commands.CooldownMapping(commands.Cooldown(rate, per), type)
        else:
            func.__commands_cooldown__ = commands.CooldownMapping(commands.Cooldown(rate, per), type)
        return func

    return decorator


def is_owner():
    async def predicate(ctx: Context):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner("You do not own this bot.")
        return True

    return check(predicate, member_permissions=["bot_owner"])


def is_guild_owner():
    async def predicate(ctx: Context):
        if ctx.author != ctx.guild.owner:
            raise NotGuildOwner
        return True

    return check(predicate, member_permissions=["guild_owner"])
