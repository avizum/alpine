"""
Cog for my servers (Lounge and Support server)
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
import re
from discord.ext import commands, tasks
from utils import AvimetryBot, AvimetryContext, PrivateServer


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
        828803974941245470: 828783296023625770
}

ROLE_MAP = {
    REACTION_ROLE_ID: REACTION_ROLES_EMOJIS,
    COLOR_ROLE_ONE: COLOR_ROLES_EMOJIS,
    COLOR_ROLE_TWO: COLOR_ROLES_EMOJIS
}


class Servers(commands.Cog, name="Servers"):
    '''
    Commands for avi's servers only.
    '''
    def __init__(self, avi):
        self.avi: AvimetryBot = avi
        self.update_count.start()
        self.guild_id = [751490725555994716, 814206001451761664]
        self.joins_and_leaves = 751967006701387827
        self.member_channel = 783960970472456232
        self.bot_channel = 783961050814611476
        self.total_channel = 783961111060938782

    def cog_check(self, ctx: AvimetryContext):
        if ctx.guild.id not in self.guild_id:
            raise PrivateServer("This command only works in a private server.")
        return True

    def get(self, channel_id: int):
        return self.avi.get_channel(channel_id)

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

    @tasks.loop(minutes=5)
    async def update_count(self):
        guild: discord.Guild = self.avi.get_guild(self.guild_id[0])
        if guild is None:
            return
        role = guild.get_role(813535792655892481)

        not_bot = [mem for mem in guild.members if not mem.bot]
        for i in not_bot:
            try:
                await i.add_roles(role)
            except Exception:
                pass

    @update_count.before_loop
    async def before_update_count(self):
        await self.avi.wait_until_ready()

    @commands.Cog.listener("on_member_update")
    async def member_update(self, before: discord.Member, after: discord.Member):
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
                return await after.edit(nick=after.name, reason='Nick can not be "avi"')
            except discord.Forbidden:
                pass

    @commands.command(
        hidden=True
    )
    async def testing(self, ctx: AvimetryContext):
        if ctx.guild.id != 814206001451761664:
            return
        role = ctx.guild.get_role(836105548457574410)
        if role in ctx.author.roles:
            return await ctx.message.add_reaction(self.avi.emoji_dictionary["red_tick"])
        await ctx.author.add_roles(role, reason="Public testing")
        await ctx.message.add_reaction(self.avi.emoji_dictionary["green_tick"])


def setup(avi):
    avi.add_cog(Servers(avi))
