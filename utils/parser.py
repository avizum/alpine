"""
Parse join messages and preview
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

import discord
import json
from tagformatter import Parser
from .context import AvimetryContext


parser = Parser(case_insensitive=True)


@parser.tag("member")
def member(env):
    return str(env.member)


@member.tag("mention", alias="ping")
def member_mention(env):
    return env.member.mention


@member.tag("name")
def member_name(env):
    return env.member.name


@member.tag("id")
def member_id(env):
    return env.member.id


@member.tag("discriminator", alias="tag")
def member_discriminator(env):
    return env.member.discriminator


@member.tag("avatar", aliases=["image", "pfp", "picture", "pic", "icon"])
def member_avatar(env):
    return str(env.member.avatar.replace(format="png", static_format="png", size=512))


@parser.tag("guild", alias="server")
def guild(env):
    return env.guild.name


@guild.tag("member_count", alias="count")
def guild_member_count(env):
    return env.guild.member_count


@guild.tag("icon", aliases=["picture", "pfp", "pic", "image"])
def guild_icon(env):
    return str(env.guild.icon.replace(format="png", static_format="png", size=512))


async def preview_message(message, ctx: AvimetryContext):
    env = {"member": ctx.author, "guild": ctx.guild}
    message = parser.parse(message, env=env)
    try:
        message = json.loads(message)
        message = discord.Embed.from_dict(message)
        return message
    except Exception:
        return message
