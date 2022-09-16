"""
[Ignition Bot]
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
from wavelink.errors import QueueException


class QueueDuplicateTrack(QueueException):
    """
    Raised when `Queue.allow_duplicates` is `False` and a duplicate track is added to the queue.
    """

    pass

class NoChannelProvided(commands.CheckFailure):
    """
    Error raised when no suitable voice channel was supplied.
    """

    pass


class IncorrectChannelError(commands.CheckFailure):
    """
    Error raised when commands are used outside of the players session channel.
    """

    pass


class NotInVoice(commands.CheckFailure):
    """
    Error raised when someone tries do to something when they are not in the voice channel.
    """

    pass


class BotNotInVoice(commands.CheckFailure):
    """
    Error raised when the bot is not in the voice channel.
    """

    pass
