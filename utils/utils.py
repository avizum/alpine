"""
Custom utilities for the bot
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
import time
import typing


def format_string(number, value):
    """
    "Humanizes" a name, Ex: 1 time, 2 times
    """
    if number == 1:
        return f"{number} {value}"
    return f"{number} {value}s"


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
        return f'<t:{int(times.timestamp())}:{format}>'
    return f'<t:{int(times.timestamp())}>'


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
