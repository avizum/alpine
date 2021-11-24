"""
Cog for my servers (Lounge and Support server)
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
import re
import datetime
import core

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

ROLE_MAP = {
    828830074080985138: {
        828446615135191100: 828437716429570128,
        828445765772509234: 828437885820076053
    }
}


class Servers(commands.Cog, name="Servers"):
    """
    Commands for bot's servers only.
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
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
        return self.bot.get_channel(channel_id)

    @core.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id in self.bot.cache.blacklist:
            return
        try:
            emojis = ROLE_MAP[payload.message_id]
        except KeyError:
            return
        guild = self.bot.get_guild(payload.guild_id)
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

    @core.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        try:
            emojis = ROLE_MAP[payload.message_id]
        except KeyError:
            return
        guild = self.bot.get_guild(payload.guild_id)
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
        guild: discord.Guild = self.bot.get_guild(self.guild_id[0])
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
        await self.bot.wait_until_ready()

    @core.command(hidden=True, aliases=["tester"])
    async def testing(self, ctx: AvimetryContext):
        """
        Gives testing role.

        This will give you access to the testing channel where you can test some features.
        """
        if ctx.guild.id != 814206001451761664:
            return
        role = ctx.guild.get_role(836105548457574410)
        if role in ctx.author.roles:
            return await ctx.author.remove_roles(role)
        await ctx.author.add_roles(role, reason="Public testing")
        await ctx.message.add_reaction(self.bot.emoji_dictionary["green_tick"])

    @testing.error
    async def testing_error(self, ctx: AvimetryContext, error):
        if isinstance(error, PrivateServer):
            return
        raise error


def setup(bot):
    bot.add_cog(Servers(bot))
