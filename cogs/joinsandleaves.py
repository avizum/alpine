"""
Cog to handle join and leave messages (if enabled)
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

import discord
import json

from discord.ext import commands
from tagformatter import Parser
from utils import AvimetryBot


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
    return str(env.member.avatar_url_as(format="png", static_format="png", size=512))


@parser.tag("guild", alias="server")
def guild(env):
    return env.guild.name


@parser.tag("name")
def guild_name(env):
    return env.guild.name


@guild.tag("member_count", alias="count")
def guild_member_count(env):
    return env.guild.member_count


@guild.tag("icon", aliases=["picture", "pfp", "pic", "image"])
def guild_icon(env):
    return str(env.guild.icon_url_as(format="png", static_format="png", size=512))


class JoinsAndLeaves(commands.Cog):
    """
    Cog for handling joins and leave messages.
    """
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    async def convert(self, message):
        try:
            message = json.loads(message)
            message = discord.Embed.from_dict(message)
            return message
        except Exception:
            return message

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = self.avi.cache.join_leave.get(member.guild.id)
        if not config:
            return
        join_channel = discord.utils.get(member.guild.channels, id=config["join_channel"])
        join_message = config["join_message"]
        join_config = config["join_enabled"]
        if not join_channel or not join_message or not join_config:
            return
        env = {
            "member": member,
            "guild": member.guild
        }
        message = parser.parse(join_message, env=env)
        final = await self.convert(message)
        if type(final) is discord.Embed:
            return await join_channel.send(embed=final)
        return await join_channel.send(final)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        config = self.avi.cache.join_leave.get(member.guild.id)
        if not config:
            return
        leave_channel = discord.utils.get(member.guild.channels, id=config["leave_channel"])
        leave_message = config["leave_message"]
        leave_config = config["leave_enabled"]
        if not leave_channel or not leave_message or not leave_config:
            return
        env = {
            "member": member,
            "guild": member.guild
        }
        message = parser.parse(leave_message, env=env)
        final = await self.convert(message)
        if type(final) is discord.Embed:
            return await leave_channel.send(embed=final)
        return await leave_channel.send(final)


def setup(avi):
    avi.add_cog(JoinsAndLeaves(avi))
