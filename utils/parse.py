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

import json
from typing import TYPE_CHECKING

import discord
from tagformatter import Parser

if TYPE_CHECKING:
    from core import Context

__all__ = ("preview_message",)

parser = Parser(case_insensitive=True)


@parser.tag("member")
def member(env) -> str:
    return str(env.member)


@member.tag("mention", alias="ping")
def member_mention(env) -> str:
    return env.member.mention


@member.tag("name")
def member_name(env) -> str:
    return env.member.name


@member.tag("id")
def member_id(env) -> int:
    return env.member.id


@member.tag("avatar", aliases=["image", "pfp", "picture", "pic", "icon"])
def member_avatar(env) -> str:
    return str(env.member.avatar.replace(format="png", static_format="png", size=512))


@parser.tag("guild", alias="server")
def guild(env) -> str:
    return env.guild.name


@guild.tag("member_count", alias="count")
def guild_member_count(env) -> int:
    return env.guild.member_count


@guild.tag("icon", aliases=["picture", "pfp", "pic", "image"])
def guild_icon(env) -> str:
    return str(env.guild.icon.replace(format="png", static_format="png", size=512))


def preview_message(message: str, ctx: Context) -> str | discord.Embed:
    env = {"member": ctx.author, "guild": ctx.guild}
    parsed = parser.parse(message, env=env)
    try:
        data = json.loads(parsed)
        return discord.Embed.from_dict(data)
    except Exception:
        return parsed
