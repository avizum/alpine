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
from typing import Any, List
from dataclasses import dataclass, field

from discord.utils import MISSING

from discord.ext import commands


@dataclass
class Flag(commands.Flag):
    name: str = MISSING
    description: str = MISSING
    aliases: List[str] = field(default_factory=list)
    attribute: str = MISSING
    annotation: Any = MISSING
    default: Any = MISSING
    max_args: int = MISSING
    override: bool = MISSING
    cast_to_dict: bool = False


def flag(
    *,
    name: str = MISSING,
    description: str = MISSING,
    aliases: List[str] = MISSING,
    default: Any = MISSING,
    max_args: int = MISSING,
    override: bool = MISSING,
) -> Any:
    return Flag(
        name=name, description=description, aliases=aliases, default=default, max_args=max_args, override=override
    )
