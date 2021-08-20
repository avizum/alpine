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
