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

from discord.ext import commands

__all__ = (
    "Blacklisted",
    "CommandDisabledChannel",
    "CommandDisabledGuild",
    "Maintenance",
    "NotGuildOwner",
)


class NotGuildOwner(commands.CheckFailure):
    def __init__(self, message=None, *args) -> None:
        message = message or "You do not own this server."
        super().__init__(message=message, *args)


class Blacklisted(commands.CheckFailure):
    def __init__(self, reason: str) -> None:
        self.reason: str = reason


class Maintenance(commands.CheckFailure):
    pass


class CommandDisabledGuild(commands.DisabledCommand):
    pass


class CommandDisabledChannel(commands.DisabledCommand):
    pass
