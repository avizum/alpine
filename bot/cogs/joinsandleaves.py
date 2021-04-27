import discord
import json
from discord.ext import commands
from tagformatter import Parser


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
        self.avi = avi

    async def convert(self, message):
        try:
            message = json.loads(message)
            message = discord.Embed.from_dict(message)
            return message
        except Exception:
            return message

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = self.avi.temp.join_leave_cache.get(member.guild.id)
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
        try:
            await join_channel.send(final)
        except Exception:
            await join_channel.send(embed=final)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        config = self.avi.temp.join_leave_cache.get(member.guild.id)
        if not config:
            return
        leave_channel = discord.utils.get(member.guild.channels, id=config["leave_channel"])
        leave_message = config["leave_message"]
        leave_config = config["leave_enabled"]
        if not leave_channel or not leave_message or not leave_config:
            return
        message = parser.parse(leave_message, env=self.env)
        final = await self.convert(message)
        try:
            await leave_channel.send(final)
        except Exception:
            await leave_channel.send(embed=final)


def setup(avi):
    avi.add_cog(JoinsAndLeaves(avi))
