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

import datetime
import json

import discord
from tagformatter import Parser

import core
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
            return discord.Embed.from_dict(message)  # type: ignore
        except Exception:
            return message

    @core.Cog.listener("on_member_join")
    @core.Cog.listener("on_test_member_join")
    async def member_join(self, member: discord.Member):
        guild = self.bot.database.get_guild(member.guild.id)
        if not guild:
            return None
        settings = guild.join_leave
        if not settings or not settings.enabled or not settings.channel_id or not settings.join_message:
            return None
        channel = self.bot.get_channel(settings.channel_id)
        message = settings.join_message

        assert isinstance(channel, discord.TextChannel)

        env = {"member": member, "guild": member.guild}
        message = parser.parse(message, env=env)
        final = self.convert(message)
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=[member])
        if isinstance(final, discord.Embed):
            return await channel.send(embed=final, allowed_mentions=allowed_mentions)
        return await channel.send(final, allowed_mentions=allowed_mentions)

    @core.Cog.listener("on_member_remove")
    @core.Cog.listener("on_test_member_remove")
    async def member_remove(self, member: discord.Member):
        guild = self.bot.database.get_guild(member.guild.id)
        if not guild:
            return None

        settings = guild.join_leave
        if not settings or not settings.enabled or not settings.channel_id or not settings.leave_message:
            return None
        channel = self.bot.get_channel(settings.channel_id)
        message = settings.leave_message

        assert isinstance(channel, discord.TextChannel)

        env = {"member": member, "guild": member.guild}
        message = parser.parse(message, env=env)
        final = self.convert(message)
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=[member])
        if isinstance(final, discord.Embed):
            return await channel.send(embed=final, allowed_mentions=allowed_mentions)
        return await channel.send(final, allowed_mentions=allowed_mentions)


async def setup(bot):
    await bot.add_cog(JoinsAndLeaves(bot))
