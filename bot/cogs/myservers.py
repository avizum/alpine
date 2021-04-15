import discord
import re
import asyncio
from discord.ext import commands, tasks
from utils.errors import PrivateServer
from utils.context import AvimetryContext


URL_REGEX = re.compile(
    r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.\
        [^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})")

REACTION_ROLE_ID = 828830074080985138
REACTION_ROLES_EMOJIS = {
    828446615135191100: 828437716429570128,
    828445765772509234: 828437885820076053
}

COLOR_ROLE_ONE = 828830077302341642
COLOR_ROLE_TWO = 828830098329174016
COLOR_ROLES_EMOJIS = {
        828803461499322419: 828783285735653407,
        828803483456897064: 828783291603746877,
        828803502284472330: 828467481236078622,
        828803518751047760: 828783292924297248,
        828803535088386080: 828783296983990272,
        828803555192078416: 828716599950311426,
        828803571566248008: 828783295382814750,
        828803590067322910: 828788247105765407,
        828803604839792661: 828788233327869994,
        828803624644771860: 828788255334858815,
        828803640004837376: 828783290281754664,
        828803656924397589: 828783293699850260,
        828803674633011253: 828783297411678240,
        828803726089256991: 828783289400950864,
        828803747755851776: 828783291279867934,
        828803769013370880: 828783297927839745,
        828803790673018960: 828783288410832916,
        828803810533179404: 828783286599024671,
        828803838387290162: 828783292504604702,
        828803863661248513: 828783287585341470,
        828803885811367966: 828448876469026846,
        828803903637422100: 828799927857053696,
        828803923799179304: 828476018439356436,
        828803974941245470: 828783296023625770,
}

ROLE_MAP = {
    REACTION_ROLE_ID: REACTION_ROLES_EMOJIS,
    COLOR_ROLE_ONE: COLOR_ROLES_EMOJIS,
    COLOR_ROLE_TWO: COLOR_ROLES_EMOJIS
}


class AvizumsLounge(commands.Cog, name="Avizum's Lounge"):
    '''
    Commands for Avizum's Lounge only.
    '''
    def __init__(self, avi):
        self.avi = avi
        self.update_count.start()
        self.guild_id = 751490725555994716
        self.joins_and_leaves = 751967006701387827
        self.member_channel = 783960970472456232
        self.bot_channel = 783961050814611476
        self.total_channel = 783961111060938782

    def cog_check(self, ctx: AvimetryContext):
        if ctx.guild.id != self.guild_id:
            raise PrivateServer("This command only works in a private server.")
        return True

    def get(self, channel_id: int):
        return self.avi.get_channel(channel_id)

# event
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        try:
            emojis = ROLE_MAP[payload.message_id]
        except KeyError:
            return
        guild = self.avi.get_guild(payload.guild_id)
        if guild is None:
            return
        try:
            role_id = emojis[payload.emoji.id]
        except KeyError:
            return

        role = guild.get_role(role_id)
        if role is None:
            return
        try:
            await payload.member.add_roles(role)
        except Exception:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        try:
            emojis = ROLE_MAP[payload.message_id]
        except KeyError:
            return
        guild = self.avi.get_guild(payload.guild_id)
        if guild is None:
            return
        try:
            role_id = emojis[payload.emoji.id]
        except KeyError:
            return
        role = guild.get_role(role_id)
        if role is None:
            return
        member = guild.get_member(payload.user_id)
        if member is None:
            return
        try:
            await member.remove_roles(role)
        except Exception:
            return

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != 810723783093911642:
            return
        if message.author == self.avi.user:
            return
        if message.attachments:
            return
        find_url = re.findall(URL_REGEX, message.content)
        if find_url:
            return
        message = await message.reply("GIFs only.")
        reference = message.reference.resolved
        await asyncio.sleep(2)
        await message.channel.delete_messages([message, reference])

    @tasks.loop(minutes=5)
    async def update_count(self):
        guild: discord.Guild = self.avi.get_guild(self.guild_id)
        if guild is None:
            return
        total = guild.member_count
        members = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])

        await self.get(self.total_channel).edit(name=f"Total Members: {total}")
        await self.get(self.member_channel).edit(name=f"Members: {members}")
        await self.get(self.bot_channel).edit(name=f"Bots: {bots}")

        role = guild.get_role(813535792655892481)

        for i in guild.members:
            if role in i.roles:
                pass
            if role not in i.roles:
                try:
                    await i.add_roles(role)
                except Exception:
                    pass

    @update_count.before_loop
    async def before_update_count(self):
        await self.avi.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == self.guild_id:
            root = member.guild.get_role(813535792655892481)
            await member.add_roles(root)

        if self.get(self.joins_and_leaves).guild.id == member.guild.id:
            join_message = discord.Embed(
                title="Member Joined",
                description=(
                    f"Hey **{str(member)}**, Welcome to **{member.guild.name}**!\n"
                    f"This server now has a total of **{member.guild.member_count}** members."
                ),
                color=discord.Color.blurple()
            )
            await self.get(self.joins_and_leaves).send(embed=join_message)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == self.guild_id:
            if self.get(self.joins_and_leaves).guild.id == member.guild.id:
                lm = discord.Embed(
                    title="Member Leave",
                    description=(
                        f"Aww, **{str(member)}** has left **{member.guild.name}**.\n"
                        f"This server now has a total of **{member.guild.member_count}** members."
                    ),
                    color=discord.Color.red()
                )
                await self.get(self.joins_and_leaves).send(embed=lm)

    @commands.Cog.listener("on_member_update")
    async def member_update(self, before, after):
        if after.guild.id != 751490725555994716:
            return
        if not after.nick:
            return
        if "avi" in after.nick.lower():
            if after == self.avi.user:
                return
            if after.id == 750135653638865017:
                return
            try:
                return await after.edit(nick=after.name, reason="Nick can not be \"avi\"")
            except discord.Forbidden:
                pass

    # Update Member Count Command
    @commands.command(
        aliases=["updatemc", "umembercount"],
        brief="Updates the member count if the count gets out of sync.",
    )
    @commands.has_permissions(administrator=True)
    async def refreshcount(self, ctx: AvimetryContext):
        channel = self.avi.get_channel(783961111060938782)
        await channel.edit(name=f"Total Members: {channel.guild.member_count}")

        channel2 = self.avi.get_channel(783960970472456232)
        true_member_count = len([m for m in channel.guild.members if not m.bot])
        await channel2.edit(name=f"Members: {true_member_count}")

        channel3 = self.avi.get_channel(783961050814611476)
        true_bot_count = len([m for m in channel.guild.members if m.bot])
        await channel3.edit(name=f"Bots: {true_bot_count}")
        await ctx.send("Member Count Updated.")


def setup(avi):
    avi.add_cog(AvizumsLounge(avi))
