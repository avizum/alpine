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

from discord.ext import commands


class TimeZoneError(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__(
            f'Timezone "{argument}" was not found. [Here]'
            "(https://gist.github.com/Soheab/3bec6dd6c1e90962ef46b8545823820d) "
            "are all the valid timezones you can use."
        )


class NotGuildOwner(commands.CheckFailure):
    def __init__(self, message=None, *args):
        message = message or "You do not own this server."
        super().__init__(message=message, *args)


class BlacklistWarn(commands.CheckFailure):
    def __init__(self, reason):
        self.reason = reason


class Blacklisted(commands.CheckFailure):
    def __init__(self, reason):
        self.reason = reason


class PrivateServer(commands.CheckFailure):
    pass


class Maintenance(commands.CheckFailure):
    pass


class CommandDisabledGuild(commands.DisabledCommand):
    """Used when command is disabled in guild"""

    pass


class CommandDisabledChannel(commands.DisabledCommand):
    """Used when command is disabled in channel"""

    pass
