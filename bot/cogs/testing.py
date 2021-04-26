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
    return str(env.member.icon_url_as(format="png", static_format="png", size=512))


class Tests(commands.Cog):
    def __init__(self, avi):
        self.avi = avi

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = discord.utils.get(member.guild.channels, id=831278962226626581)
        message = (
            '''
            {
                "title": "Member Joined",
                "description": "Hey {member.name}, welcome to {server}!\nThere are now {server.count} members here.",
                "author": {
                    "name": "{member}",
                    "icon_url": "{member.icon}"
                },
                "color": 7506394,
                "footer": {
                    "text": "Member #{server.count}"
                }
            }
            ''')
        message = "Hey {member.ping}, welcome to {server}! There are now {server.member_count} members in {server}. "
        env = {
            "member": member,
            "guild": member.guild
        }
        message = parser.parse(message, env=env)
        try:
            message = json.loads(message)
            embed = discord.Embed.from_dict(message)
            return await channel.send(embed=embed)
        except Exception:
            await channel.send(message)

    @commands.command()
    async def disp(self, ctx):
        self.avi.dispatch("member_join", member=ctx.author)

    """
import random
from tagformatter import Parser

parser = Parser(case_insensitive=True)

@parser.tag('user')
def user_tag(env):
  return env.user.name

# "Sub-tags" - in reality these just "add attributes to the tags."
@user_tag.tag('mention', alias='ping')  # Aliases
def user_mention_tag(env):
  return env.user.mention

# Example of basic converters and args
@parser.tag('random', alias='rng')
def random_number_tag(env, low: int, high: int):
  return random.randint(low, high)

# Implement into our bot
@bot.command()
async def do_tags(ctx, *, tags):
  env = { "user": ctx.author }
  await ctx.send(parser.parse(tags, env))
    """


def setup(avi):
    avi.add_cog(Tests(avi))
