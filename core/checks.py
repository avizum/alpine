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

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Coroutine, Literal, TYPE_CHECKING, TypeVar

import discord
from discord.ext import commands
from discord.ext.commands import NoPrivateMessage

from .alpine import OWNER_IDS
from .core import Command
from .exceptions import NotGuildOwner

if TYPE_CHECKING:
    from discord.ext.commands._types import Check, UserCheck

    from .context import Context
    from .core import Bot


__all__ = (
    "bot_has_permissions",
    "check",
    "cooldown",
    "describe",
    "has_permissions",
    "is_guild_owner",
    "is_owner",
)


T = TypeVar("T")
Coro = Coroutine[Any, Any, T]
CoroFunc = Callable[..., Coro[Any]]
CommandFunc = Command[Any, ..., Any] | CoroFunc


def check(predicate: UserCheck[Context[Bot]]) -> Check[Context[Bot]]:
    def decorator(func: Command[Any, ..., Any] | CoroFunc) -> Command[Any, ..., Any] | CoroFunc:
        if isinstance(func, Command):
            func.checks.append(predicate)  # type: ignore
        else:
            if not hasattr(func, "__commands_checks__"):
                func.__commands_checks__ = []

            func.__commands_checks__.append(predicate)

        return func

    if inspect.iscoroutinefunction(predicate):
        decorator.predicate = predicate
    else:

        @functools.wraps(predicate)
        async def wrapper(ctx: Context[Bot]):
            return predicate(ctx)

        decorator.predicate = wrapper

    return decorator  # type: ignore


def _validate_permissions(**perms: bool) -> None:
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")


def _permissions_wrapper(kind: Literal["permissions", "bot_permissions"], **perms: bool) -> Any:
    def predicate(ctx: Context[Any]) -> bool:
        permissions: discord.Permissions = getattr(ctx, kind)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        exc = commands.MissingPermissions
        if kind == "bot_permissions":
            exc = commands.BotMissingPermissions

        raise exc(missing)

    if inspect.iscoroutinefunction(predicate):
        return predicate

    @functools.wraps(predicate)
    async def wrapper(ctx: Context):
        return predicate(ctx)

    return wrapper


def _member_permissions(func: CommandFunc, **perms: bool) -> CommandFunc:
    permissions = [perm for perm, value in perms.items() if value]
    app_command_permissions = discord.Permissions(**perms)

    if isinstance(func, Command):
        func.checks.append(_permissions_wrapper("permissions", **perms))
        func.member_permissions = permissions
        if getattr(func, "__commands_is_hybrid__", None):
            app_command = getattr(func, "app_command", None)
            if app_command:
                app_command.default_permissions = app_command_permissions
    else:
        if not hasattr(func, "__member_permissions__"):
            func.__member_permissions__ = []
        if not hasattr(func, "__commands_checks__"):
            func.__commands_checks__ = []
        func.__member_permissions__.extend(permissions)
        func.__commands_checks__.append(_permissions_wrapper("permissions", **perms))
        func.__discord_app_commands_default_permissions__ = app_command_permissions

    return func


def _bot_permissions(func: CommandFunc, **perms: bool) -> CommandFunc:
    permissions = [perm for perm, value in perms.items() if value]

    if isinstance(func, Command):
        func.checks.append(_permissions_wrapper("bot_permissions", **perms))
        func.member_permissions = permissions
    else:
        if not hasattr(func, "__bot_permissions__"):
            func.__bot_permissions__ = []
        if not hasattr(func, "__commands_checks__"):
            func.__commands_checks__ = []
        func.__bot_permissions__.extend(permissions)
        func.__commands_checks__.append(_permissions_wrapper("bot_permissions", **perms))

    return func


def has_permissions(**perms: bool) -> Callable[[CommandFunc], CommandFunc]:
    _validate_permissions(**perms)

    def decorator(func: CommandFunc) -> CommandFunc:
        return _member_permissions(func, **perms)

    return decorator


def bot_has_permissions(**perms: bool) -> Callable[[CommandFunc], CommandFunc]:
    _validate_permissions(**perms)

    def decorator(func: CommandFunc) -> CommandFunc:
        return _bot_permissions(func, **perms)

    return decorator


def cooldown(
    rate: int, per: float, type: commands.BucketType | Callable[[Context[Bot]], Any] = commands.BucketType.user
) -> Callable[[T], T]:
    default_cooldown = commands.Cooldown(rate, per)

    def decorator(func: CommandFunc) -> CommandFunc:
        def owner_cd(message: discord.Message):
            return None if message.author.id in OWNER_IDS else default_cooldown

        mapping = commands.DynamicCooldownMapping(owner_cd, type)  # type: ignore
        mapping._cooldown = default_cooldown

        if isinstance(func, Command):
            func._buckets = mapping  # type: ignore
        else:
            func.__commands_cooldown__ = mapping
        return func

    return decorator  # type: ignore


def is_owner():
    async def predicate(ctx: Context):
        if not await ctx.bot.is_owner(ctx.author):
            raise commands.NotOwner("You do not own this bot.")
        return True

    def decorator(func: CommandFunc) -> CommandFunc:
        if isinstance(func, Command):
            func.checks.append(predicate)  # type: ignore
            func.member_permissions = ["bot_owner"]
        else:
            if not hasattr(func, "__commands_checks__"):
                func.__commands_checks__ = []
            func.__commands_checks__.append(predicate)
            if not hasattr(func, "__member_permissions__"):
                func.__member_permissions__ = []
            func.__member_permissions__.append("bot_owner")
        return func

    if inspect.iscoroutinefunction(predicate):
        decorator.predicate = predicate
    else:

        @functools.wraps(predicate)
        async def wrapper(ctx: Context):
            return predicate(ctx)

        decorator.predicate = wrapper

    return decorator


def is_guild_owner():
    def predicate(ctx: Context):
        if not ctx.guild:
            raise NoPrivateMessage
        if ctx.author != ctx.guild.owner:
            raise NotGuildOwner
        return True

    def decorator(func: CommandFunc) -> CommandFunc:
        if isinstance(func, Command):
            func.checks.append(predicate)  # type: ignore
            func.member_permissions = ["guild_owner"]
        else:
            if not hasattr(func, "__commands_checks__"):
                func.__commands_checks__ = []
            func.__commands_checks__.append(predicate)
            if not hasattr(func, "__member_permissions__"):
                func.__member_permissions__ = []
            func.__member_permissions__.append("guild_owner")
        return func

    if inspect.iscoroutinefunction(predicate):
        decorator.predicate = predicate
    else:

        @functools.wraps(predicate)
        async def wrapper(ctx: Context):
            return predicate(ctx)

        decorator.predicate = wrapper
    return decorator


describe = discord.app_commands.describe
