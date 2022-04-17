"""
Custom command class for discord.ext.commands
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


import datetime
from typing import TYPE_CHECKING, Any, TypeVar, ParamSpec, Concatenate, Callable, overload

import discord
from discord.ext import commands
from discord.ext.commands import DisabledCommand, CheckFailure
from discord.ext.commands._types import CogT


if TYPE_CHECKING:
    from .avimetry import Bot
    from discord.ext.commands._types import ContextT, Coro

MISSING = discord.utils.MISSING

T = TypeVar('T')
GroupT = TypeVar('GroupT', bound='Group')
CommandT = TypeVar('CommandT', bound='Command')

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


def to_list(thing) -> list[str]:
    return [thing] if isinstance(thing, str) else list(thing)


class Command(commands.Command):
    def __init__(self, func, **kwargs) -> None:
        self.member_permissions = to_list(
            kwargs.get("member_permissions")
            or getattr(func, "member_permissions", ["send_messages"])
            or kwargs.get("extras", {}).get("member_permissions")
        )
        self.bot_permissions = to_list(
            kwargs.get("bot_permissions")
            or getattr(func, "bot_permissions", ["send_messages"])
            or kwargs.get("extras", {}).get("bot_permissions")
        )
        super().__init__(func, **kwargs)
        if not self._buckets._cooldown:
            self._buckets = commands.CooldownMapping(commands.Cooldown(1, 3), commands.BucketType.user)
            self._buckets._cooldown = commands.Cooldown(1, 3)

    def __repr__(self) -> str:
        return f"<core.Command name={self.qualified_name}>"

    async def can_run(self, ctx: commands.Context) -> bool:
        if not self.enabled:
            raise DisabledCommand(f"{self.name} command is disabled")

        original = ctx.command
        ctx.command = self

        try:
            if not await ctx.bot.can_run(ctx):
                raise CheckFailure(f"The global check functions for command {self.qualified_name} failed.")

            cog = self.cog
            if cog is not None:
                local_check = Cog._get_overridden_method(cog.cog_check)
                if local_check is not None:
                    ret = await discord.utils.maybe_coroutine(local_check, ctx)
                    if not ret:
                        return False

            predicates = self.checks
            if not predicates:
                # since we have no checks, then we just return True.
                return True

            return await discord.utils.async_all(predicate(ctx) for predicate in predicates)  # type: ignore
        finally:
            ctx.command = original


class Group(Command, commands.Group):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.invoke_without_command = kwargs.get("invoke_without_command", True)

    def command(self, *args, **kwargs) -> Command:
        def decorator(func):
            kwargs.setdefault("parent", self)
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(self, *args, **kwargs) -> Group:
        def decorator(func):
            kwargs.setdefault("parent", self)
            result = group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator


class Cog(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.load_time: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)

if TYPE_CHECKING:
    # Using a class to emulate a function allows for overloading the inner function in the decorator.

    class _CommandDecorator:
        @overload
        def __call__(self, func: Callable[Concatenate[CogT, ContextT, P], Coro[T]], /) -> Command[CogT, P, T]:
            ...

        @overload
        def __call__(self, func: Callable[Concatenate[ContextT, P], Coro[T]], /) -> Command[None, P, T]:
            ...

        def __call__(self, func: Callable[..., Coro[T]], /) -> Any:
            ...

    class _GroupDecorator:
        @overload
        def __call__(self, func: Callable[Concatenate[CogT, ContextT, P], Coro[T]], /) -> Group[CogT, P, T]:
            ...

        @overload
        def __call__(self, func: Callable[Concatenate[ContextT, P], Coro[T]], /) -> Group[None, P, T]:
            ...

        def __call__(self, func: Callable[..., Coro[T]], /) -> Any:
            ...


@overload
def command(
    name: str = ...,
    **attrs: Any,
) -> _CommandDecorator:
    ...


@overload
def command(
    name: str = ...,
    cls: type[CommandT] = ...,
    **attrs: Any,
) -> Callable[
    [
        Callable[Concatenate[ContextT, P], Coro[Any]] |
        Callable[Concatenate[CogT, ContextT, P], Coro[Any]]
    ],
    CommandT,
]:
    ...

def command(
    name: str = MISSING,
    cls: type[Command[Any, ..., Any]] = None,
    **kwargs
) -> Any:
    if cls is None:
        cls = Command

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError("Callback is already a command")
        return cls(func, name=name, **kwargs)

    return decorator


@overload
def group(
    name: str = ...,
    **attrs: Any,
) -> _GroupDecorator:
    ...


@overload
def group(
    name: str = ...,
    cls: type[GroupT] = ...,
    **attrs: Any,
) -> Callable[
    [
        Callable[Concatenate[CogT, ContextT, P], Coro[Any]] |
        Callable[Concatenate[ContextT, P], Coro[Any]],
    ],
    GroupT,
]:
    ...


def group(
    name: str = MISSING,
    cls: type[Group[Any, ..., Any]] = MISSING,
    **kwargs: Any,
) -> Any:
    return command(name=name, cls=Group, **kwargs)
