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

import datetime
import discord
import json
import core

from tagformatter import Parser
from core import Bot


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


@parser.tag("name")
def guild_name(env):
    return env.guild.name


@guild.tag("member_count", alias="count")
def guild_member_count(env):
    return env.guild.member_count


@guild.tag("icon", aliases=["picture", "pfp", "pic", "image"])
def guild_icon(env):
    return str(env.guild.icon_url_as(format="png", static_format="png", size=512))


class JoinsAndLeaves(core.Cog):
    """
    Cog for handling joins and leave messages.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)

    def convert(self, message: str) -> discord.Embed | str:
        try:
            message = json.loads(message)
            message = discord.Embed.from_dict(message)  # type: ignore
            return message
        except Exception:
            return message

    @core.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = self.bot.cache.join_leave.get(member.guild.id)
        if not config:
            return
        join_channel: discord.TextChannel = self.bot.get_channel(config["join_channel"])  # type: ignore
        join_message = config["join_message"]
        join_config = config["join_enabled"]
        if not join_channel or not join_message or not join_config:
            return
        env = {"member": member, "guild": member.guild}
        message = parser.parse(join_message, env=env)
        final = self.convert(message)
        am = discord.AllowedMentions(everyone=False, users=True)
        if type(final) is discord.Embed:
            return await join_channel.send(embed=final, allowed_mentions=am)
        if type(final) is str:
            return await join_channel.send(final, allowed_mentions=am)

    @core.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        config = self.bot.cache.join_leave.get(member.guild.id)
        if not config:
            return
        leave_channel: discord.TextChannel = self.bot.get_channel(config["leave_channel"])  # type: ignore
        leave_message = config["leave_message"]
        leave_config = config["leave_enabled"]
        if not leave_channel or not leave_message or not leave_config:
            return
        env = {"member": member, "guild": member.guild}
        message = parser.parse(leave_message, env=env)
        final = self.convert(message)
        if type(final) is discord.Embed:
            return await leave_channel.send(embed=final)
        if type(final) is str:
            return await leave_channel.send(final)


async def setup(bot):
    await bot.add_cog(JoinsAndLeaves(bot))
