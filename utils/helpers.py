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

import re
import time
from datetime import datetime
from typing import Any

__all__ = (
    "EMOJI_REGEX",
    "URL_REGEX",
    "Timer",
    "format_list",
    "format_seconds",
    "format_string",
    "timestamp",
)


URL_REGEX = re.compile(r"\b(?:https?):\/\/[-A-Za-z0-9+&@#\/%?=~_|!:,.;]*[-A-Za-z0-9+&@#\/%=~_|]")
EMOJI_REGEX: re.Pattern = re.compile(r"<(?P<animated>a?):(?P<name>\w{2,32}):(?P<id>[\d]{18,22})>")


def format_string(number: int, value: str) -> str:
    """
    "Humanizes" a name, Ex: 1 time, 2 times
    """
    return f"{number} {value}" if number == 1 else f"{number} {value}s"


def format_list(item_list: list[Any], *, seperator: str = ", ", last: str = "and") -> str | list[Any]:
    """
    Makes a list easier to read
    """
    if not item_list:
        return item_list
    if len(item_list) == 1:
        return item_list[0]
    if len(item_list) == 2:
        return f" {last} ".join(item_list)
    return f"{seperator.join(str(item) for item in item_list[:-1])} {last} {item_list[-1]}"


class Timer:
    __slots__ = ("end_time", "start_time")

    def __init__(self) -> None:
        self.start_time: float | None = None
        self.end_time: float | None = None

    def __enter__(self):
        self.start()
        return self

    async def __aenter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.stop()

    async def __aexit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.stop()

    def start(self) -> None:
        self.start_time = time.perf_counter()

    def stop(self) -> None:
        self.end_time = time.perf_counter()

    def __str__(self) -> str:
        return str(self.total_time)

    def __int__(self) -> int:
        return int(self.total_time)

    def __repr__(self) -> str:
        return f"<Timer time={self.total_time}>"

    @property
    def total_time(self) -> float:
        if self.start_time is None:
            raise ValueError("Timer has not been started")
        if self.end_time is None:
            raise ValueError("Timer has not been stopped")
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
        hour = f"{hours}h " if hours != 0 or days != 0 else ""
        minsec = f"{minutes}m {seconds}s"
        return f"{day}{hour}{minsec}"
    day = f"{days:02d}:" if days != 0 else ""
    hour = f"{hours:02d}:" if hours != 0 or days != 0 else ""
    minsec = f"{minutes:02d}:{seconds:02d}"
    return f"{day}{hour}{minsec}"


class timestamp:  # noqa: N801
    def __init__(self, datetime: datetime) -> None:
        self.datetime: datetime = datetime

    def __format__(self, format_spec: str = "f"):
        timestamp = int(self.datetime.timestamp())
        if format_spec not in ["t", "T", "d", "D", "f", "F", "R"]:
            format_spec = "f"
        return f"<t:{timestamp}:{format_spec}>"
