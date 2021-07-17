"""
Custom command class for discord.ext.commands
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
import functools
import inspect
import discord

from discord.ext import commands


class AvimetryCommand(commands.Command):
    def __init__(self, func, **kwargs):
        super().__init__(func, **kwargs)
        self.user_permissions = kwargs.get('user_permissions', 'Send Messages')
        self.bot_permissions = kwargs.get('bot_permissions', 'Send Messages')


class AvimetryGroup(AvimetryCommand, commands.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoke_without_command = kwargs.pop('invoke_without_command')


def command(name=None, cls=None, **kwargs):
    if cls is None:
        cls = AvimetryCommand

    def decorator(func):
        if isinstance(func, AvimetryCommand):
            raise TypeError('Callback is already a command')
        return cls(func, name=name, **kwargs)
    return decorator


def group(name=None, **kwargs):
    return command(name=name, cls=AvimetryGroup, **kwargs)


def check(predicate):
    def decorator(func):
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

    def predicate(ctx):
        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise commands.MissingPermissions(missing)
    return check(predicate)


def bot_has_guild_permissions(**perms):
    invalid = set(perms) - set(discord.Permissions.VALID_FLAGS)
    if invalid:
        raise TypeError(f"Invalid permission(s): {', '.join(invalid)}")

    def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage

        permissions = ctx.me.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise commands.BotMissingPermissions(missing)

    return check(predicate)
