"""
[Avimetry Bot]
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

import discord
import re
import datetime
import core

from discord.ext import commands, tasks
from core import Bot, Context
from utils import Emojis


URL_REGEX = re.compile(
    r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.\
        [^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
)


class PrivateServer(commands.CheckFailure):
    pass


class ButtonRole(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        style=discord.ButtonStyle.blurple,
        label="General Channels",
        custom_id="828437885820076053",
    )
    async def general_channels(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.guild_id != 751490725555994716:
            return
        guild = interaction.guild
        role = guild.get_role(int(button.custom_id))
        member = interaction.user
        if isinstance(member, discord.User):
            return
        if role in member.roles:
            await member.remove_roles(role)
            return await interaction.response.send_message(
                "You have been removed access from the General Channels.",
                ephemeral=True,
            )
        await member.add_roles(role)
        return await interaction.response.send_message("You now have access to the General Channels.", ephemeral=True)

    @discord.ui.button(
        style=discord.ButtonStyle.blurple,
        label="Avimetry Support",
        custom_id="927077897318047854",
    )
    async def avimetry_channels(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.guild_id != 751490725555994716:
            return
        guild = interaction.guild
        role = guild.get_role(int(button.custom_id))
        member = interaction.user
        if isinstance(member, discord.User):
            return
        if role in member.roles:
            await member.remove_roles(role)
            return await interaction.response.send_message(
                "You have been removed access from the Avimetry Support Channels.",
                ephemeral=True,
            )
        await member.add_roles(role)
        return await interaction.response.send_message("You now have access to the Avimetry Channels.", ephemeral=True)


class Servers(core.Cog):
    """
    Commands for bot's servers only.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.update_count.start()
        self.guild_id = [751490725555994716, 814206001451761664]
        self.joins_and_leaves = 751967006701387827
        self.member_channel = 783960970472456232
        self.bot_channel = 783961050814611476
        self.total_channel = 783961111060938782
        if ButtonRole() not in self.bot.persistent_views:
            bot.add_view(ButtonRole())

    def cog_check(self, ctx: Context):
        if ctx.guild.id not in self.guild_id:
            raise PrivateServer("This command only works in a private server.")
        return True

    def get(self, channel_id: int):
        return self.bot.get_channel(channel_id)

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
    async def testing(self, ctx: Context):
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
        await ctx.message.add_reaction(Emojis.GREEN_TICK)

    @testing.error
    async def testing_error(self, ctx: Context, error):
        if isinstance(error, PrivateServer):
            return
        raise error


async def setup(bot):
    await bot.add_cog(Servers(bot))
