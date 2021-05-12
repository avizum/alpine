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

def format_string(number, value):
    """
    "Humanizes" a name, Ex: 1 time, 2 times
    """
    if number == 1:
        return f"{number} {value}"
    else:
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
