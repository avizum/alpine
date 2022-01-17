"""
Custom utilities for the bot
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
import time
import typing


def format_string(number, value):
    """
    "Humanizes" a name, Ex: 1 time, 2 times
    """
    return f"{number} {value}" if number == 1 else f"{number} {value}s"


def format_list(list):
    """
    Makes a list easier to read
    """
    if not list:
        return list
    if len(list) == 1:
        return list[0]
    if len(list) == 2:
        return " and ".join(list)
    return f"{', '.join(str(item) for item in list[:-1])} and {list[-1]}"


def timestamp(times: datetime.datetime, format: typing.Optional[str] = None):
    if format:
        return f"<t:{int(times.replace(tzinfo=datetime.timezone.utc).timestamp())}:{format}>"
    return f"<t:{int(times.replace(tzinfo=datetime.timezone.utc).timestamp())}>"


class Timer:
    __slots__ = ("start_time", "end_time")

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start()
        return self

    async def __aenter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    async def __aexit__(self, exc_type, exc_value, exc_traceback):
        self.stop()

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.end_time = time.perf_counter()

    def __str__(self):
        return str(self.total_time)

    def __int__(self):
        return int(self.total_time)

    def __repr__(self):
        return f"<Timer time={self.total_time}>"

    @property
    def total_time(self):
        return self.end_time - self.start_time


# The following code is not mine Thanks Axel :)
# https://github.com/Axelancerr/Life/blob/508e1e9c5b02f56f76a53a2cfd9b521ddacdd8f3/Life/utilities/utils.py#L51-L64
def format_seconds(seconds: float, *, friendly: bool = False) -> str:

    seconds = round(seconds)

    minute, second = divmod(seconds, 60)
    hour, minute = divmod(minute, 60)
    day, hour = divmod(hour, 24)

    days, hours, minutes, seconds = (
        round(day),
        round(hour),
        round(minute),
        round(second),
    )

    if friendly:
        day = f"{days}d " if days != 0 else ""
        hour = f"{hours}h " if hours != 0 or not days == 0 else ""
        minsec = f"{minutes}m {seconds}s"
        return f"{day}{hour}{minsec}"
    day = f"{days:02d}:" if days != 0 else ""
    hour = f"{hours:02d}:" if hours != 0 or days != 0 else ""
    minsec = f"{minutes:02d}:{seconds:02d}"
    return f"{day}{hour}{minsec}"


def format_times(number: int) -> str:
    if number == 1:
        return "once"
    if number == 2:
        return "twice"
    return f"{number} times"
