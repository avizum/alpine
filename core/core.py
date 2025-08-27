"""
[Alpine Bot]
Copyright (C) 2021 - 2025 avizum

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
from typing import Any, Callable, Concatenate, Generic, Literal, overload, ParamSpec, TYPE_CHECKING, TypeVar, Unpack

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.hybrid import HybridAppCommand
from discord.utils import MISSING

if TYPE_CHECKING:
    from discord.ext.commands import Context
    from discord.ext.commands._types import Coro
    from discord.ext.commands.core import _CommandDecoratorKwargs, _GroupDecoratorKwargs
    from discord.ext.commands.hybrid import _HybridCommandDecoratorKwargs, _HybridGroupDecoratorKwargs

    from .alpine import Bot

__all__ = (
    "Cog",
    "Command",
    "Group",
    "GroupCog",
    "HybridCommand",
    "HybridGroup",
    "command",
    "group",
)

P = ParamSpec("P")
T = TypeVar("T")
CogT = TypeVar("CogT", bound="Cog | None")
GroupT = TypeVar("GroupT", bound="Group[Any, ..., Any]")
CommandT = TypeVar("CommandT", bound="Command[Any, ..., Any]")


def to_list(thing) -> list[str]:
    return [thing] if isinstance(thing, str) else list(thing)


default_cooldown = commands.Cooldown(3, 15)


def owner_cd(message: discord.Message):
    bot = message._state._get_client()
    return None if message.author.id in bot.owner_ids else default_cooldown  # type: ignore


mapping = commands.DynamicCooldownMapping(owner_cd, commands.BucketType.user)
mapping._cooldown = default_cooldown


class Command(commands.Command, Generic[CogT, P, T]):
    def __init__(
        self,
        func: Callable[Concatenate[CogT, Context[Any], P], Coro[T]] | Callable[Concatenate[Context[Any], P], Coro[T]],
        /,
        **kwargs: Any,
    ) -> None:
        extras = kwargs.get("extras", {})
        try:
            member_permissions = func.__member_permissions__
        except AttributeError:
            member_permissions = kwargs.get("member_permissions") or extras.get("member_permissions")
        self.member_permissions: list[str] | None = member_permissions

        try:
            bot_permissions = func.__bot_permissions__
        except AttributeError:
            bot_permissions = kwargs.get("bot_permissions") or extras.get("bot_permissions")
        self.bot_permissions: list[str] | None = bot_permissions

        super().__init__(func, **kwargs)
        if not self._buckets._cooldown:
            cd = commands.Cooldown(3, 15)
            self._buckets = commands.DynamicCooldownMapping(owner_cd, commands.BucketType.user)  # type: ignore
            self._buckets._cooldown = cd

    def __repr__(self) -> str:
        return f"<Command name={self.qualified_name}>"


class Group(commands.Group, Command[CogT, P, T]):
    def __init__(self, *args, **kwargs) -> None:
        self.invoke_without_command = kwargs.get("invoke_without_command", True)
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return f"<Group name={self.qualified_name}>"

    def command(
        self,
        name: str = MISSING,
        hybrid: bool = False,
        **attrs: Any,
    ) -> Callable[..., Command | HybridCommand]:
        def decorator(func):
            attrs.setdefault("parent", self)
            result = command(name=name, hybrid=hybrid, **attrs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(
        self,
        name: str = MISSING,
        hybrid: bool = False,
        **attrs: Any,
    ) -> Callable[..., Group | HybridGroup]:
        def decorator(func):
            attrs.setdefault("parent", self)
            result = group(name=name, hybrid=hybrid, **attrs)(func)
            self.add_command(result)
            return result

        return decorator


class HybridCommand(commands.HybridCommand, Command[CogT, P, T]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Prevent the lib from creating a HybridAppCommand
        super().__init__(*args, with_app_command=False, **kwargs)
        self.with_app_command: bool = kwargs.pop("with_app_command", True)
        self.app_command_name: str | app_commands.locale_str = kwargs.pop("app_command_name", MISSING)
        hybrid_name = self.name if self.app_command_name is MISSING else self.app_command_name
        self.app_command = HybridAppCommand(self, hybrid_name) if self.with_app_command else None
        if self.app_command:
            self.app_command.guild_only = True


class HybridGroup(commands.HybridGroup, Group):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # We let the lib create the app command here beacuse it does not have a custom class
        # like HybridCommand. So we will just edit the command at runtime.
        self.app_command_name: str | app_commands.locale_str = kwargs.pop("app_command_name", MISSING)

        app_command: app_commands.Group | None = getattr(self, "app_command", None)
        if app_command:
            name, name_locale = (
                (self.app_command_name.message, self.app_command_name)
                if isinstance(self.app_command_name, app_commands.locale_str)
                else (self.app_command_name, None)
            )
            if name is not MISSING:
                app_command.name = name
            app_command._locale_name = name_locale
            app_command.guild_only = True


class Cog(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.load_time: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    def __repr__(self) -> str:
        return f"<Cog name={self.qualified_name}>"


class GroupCog(commands.GroupCog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.load_time: datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    def __repr__(self) -> str:
        return f"<Group Cog name={self.qualified_name}>"


@overload
def command(
    name: str = ..., *, hybrid: Literal[True], **kwargs: Unpack[_HybridCommandDecoratorKwargs]  # type: ignore
) -> Callable[..., HybridCommand]: ...


@overload
def command(
    name: str = ..., *, hybrid: Literal[False], **kwargs: Unpack[_CommandDecoratorKwargs]
) -> Callable[..., Command]: ...


@overload
def command(
    name: str = ...,
    *,
    cls: type[Command] = ...,
    hybrid: bool = ...,
    **kwargs: Any,
) -> Callable[..., Command]: ...


def command(
    name: str = MISSING,
    *,
    cls: type[Command[Any, ..., Any]] = MISSING,
    hybrid: bool = False,
    **kwargs: Any,
) -> Callable[..., Command | HybridCommand]:
    if cls is MISSING:
        cls = HybridCommand if hybrid else Command

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError("Callback is already a command.")
        return cls(func, name=name, **kwargs)

    return decorator


@overload
def group(
    name: str = ..., *, hybrid: Literal[True], **kwargs: Unpack[_HybridGroupDecoratorKwargs]  # type: ignore
) -> Callable[..., HybridGroup]: ...


@overload
def group(
    name: str = ..., *, hybrid: Literal[False], **kwargs: Unpack[_GroupDecoratorKwargs]
) -> Callable[..., Group[Any, ..., Any]]: ...


@overload
def group(
    name: str = ...,
    *,
    cls: type[Group[Any, ..., Any]] = ...,
    hybrid: bool = ...,
    **kwargs: Any,
) -> Callable[..., Group[Any, ..., Any]]: ...


def group(
    name: str = MISSING,
    *,
    cls: type[Group[Any, ..., Any]] = MISSING,
    hybrid: bool = False,
    **kwargs: Any,
) -> Callable[..., Group[Any, ..., Any] | HybridGroup]:
    if cls is MISSING:
        cls = HybridGroup if hybrid else Group

    def decorator(func):
        if isinstance(func, Group):
            raise TypeError("Callback is already a group.")
        return cls(func, name=name, **kwargs)

    return decorator
