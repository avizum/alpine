from .context import AvimetryContext
import discord
import json
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


async def preview_message(message, ctx: AvimetryContext):
    env = {
        "member": ctx.author,
        "guild": ctx.guild
    }
    message = parser.parse(message, env=env)
    try:
        message = json.loads(message)
        message = discord.Embed.from_dict(message)
        return message
    except Exception:
        return message
