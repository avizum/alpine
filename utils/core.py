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
import datetime

from discord.ext import commands


class AvimetryCommand(commands.Command):
    def __init__(self, func, **kwargs):
        try:
            user_permissions = func.user_permissions
        except AttributeError:
            user_permissions = kwargs.get('user_permissions', 'Send Messages')
        finally:
            if isinstance(user_permissions, str):
                self.user_permissions = [user_permissions]
            elif isinstance(user_permissions, dict):
                self.user_permissions = list(user_permissions)
            elif isinstance(user_permissions, list):
                self.user_permissions = user_permissions
        try:
            bot_permissions = func.bot_permissions
        except AttributeError:
            bot_permissions = kwargs.get('bot_permissions', 'Send Messages')
        finally:
            if isinstance(bot_permissions, str):
                self.bot_permissions = [bot_permissions]
            elif isinstance(bot_permissions, dict):
                self.bot_permissions = list(bot_permissions)
            elif isinstance(bot_permissions, list):
                self.bot_permissions = bot_permissions
        super().__init__(func, **kwargs)
        if not self._buckets._cooldown:
            self._buckets._cooldown = commands.Cooldown(1, 3, commands.BucketType.user)


class AvimetryGroup(AvimetryCommand, commands.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoke_without_command = kwargs.get('invoke_without_command', True)

    def command(self, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(self, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
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
            raise TypeError('Callback is already a command')
        return cls(func, name=name, **kwargs)
    return decorator


def group(name=None, **kwargs):
    return command(name=name, cls=AvimetryGroup, **kwargs)


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
