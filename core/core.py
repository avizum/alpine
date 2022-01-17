"""
Custom command class for discord.ext.commands
Copyright (C) 2021 - present avizum

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

import datetime
import discord

from discord.ext import commands
from discord.ext.commands import DisabledCommand, CheckFailure


def to_list(thing):
    if isinstance(thing, str):
        return [thing]
    return list(thing)


class AvimetryCommand(commands.Command):
    def __init__(self, func, **kwargs):
        self.user_permissions = to_list(
            kwargs.get("user_permissions")
            or getattr(func, "user_permissions", ["send_messages"])
            or kwargs.get("extras", {}).get("user_permissions")
        )
        self.bot_permissions = to_list(
            kwargs.get("bot_permissions")
            or getattr(func, "bot_permissions", ["send_messages"])
            or kwargs.get("extras", {}).get("bot_permissions")
        )
        super().__init__(func, **kwargs)
        if not self._buckets._cooldown:
            self._buckets = commands.CooldownMapping(
                commands.Cooldown(1, 3), commands.BucketType.user
            )
            self._buckets._cooldown = commands.Cooldown(1, 3)

    async def can_run(self, ctx: commands.Context) -> bool:
        # always allow owner to run any command
        if await ctx.bot.is_owner(ctx.author):
            return True

        if not self.enabled:
            raise DisabledCommand(f"{self.name} command is disabled")

        original = ctx.command
        ctx.command = self

        try:
            if not await ctx.bot.can_run(ctx):
                raise CheckFailure(
                    f"The global check functions for command {self.qualified_name} failed."
                )

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


class AvimetryGroup(AvimetryCommand, commands.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoke_without_command = kwargs.get("invoke_without_command", True)

    def command(self, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault("parent", self)
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(self, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault("parent", self)
            result = group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator


class Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(tz=datetime.timezone.utc)


def command(name=None, cls=None, **kwargs):
    if cls is None:
        cls = AvimetryCommand

    def decorator(func):
        if isinstance(func, AvimetryCommand):
            raise TypeError("Callback is already a command")
        return cls(func, name=name, **kwargs)

    return decorator


def group(name=None, **kwargs):
    return command(name=name, cls=AvimetryGroup, **kwargs)
