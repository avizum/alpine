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

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from core import Context

__all__ = (
    "DefaultReason",
    "ModReason",
    "default_reason",
)


class ModReason(commands.Converter, str):
    def __init__(self):
        self.reason: str = ""
        super().__init__()

    @property
    def blacklist(self) -> str:
        return self.reason.replace(":\u200b ", "|\u200b|")

    async def convert(self, ctx: Context, argument=None) -> str:
        reason = f"{ctx.author}:\u200b {argument}"

        if len(reason) > 512:
            raise commands.BadArgument(f"Reason is too long ({len(reason)}/512)")
        self.reason = reason
        return reason


def default_reason(ctx: Context) -> str:
    return f"{ctx.author}: No reason was provided."


DefaultReason = commands.parameter(
    default=default_reason,
    displayed_default="<No reason provided.>",
    converter=ModReason,
    description="Reason for the action.",
)
