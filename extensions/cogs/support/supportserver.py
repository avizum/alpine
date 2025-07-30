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

import discord

import core
from core import Bot


class ButtonRole(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        style=discord.ButtonStyle.blurple,
        label="General Channels",
        custom_id="828437885820076053",
    )
    async def general_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        if button.custom_id != "828437885820076053":
            return await interaction.response.defer()
        if interaction.guild is None or interaction.guild_id != 751490725555994716:
            return await interaction.response.defer()
        role = interaction.guild.get_role(int(button.custom_id))
        if role is None:
            return await interaction.response.defer()
        member = interaction.user
        if isinstance(member, discord.User):
            return await interaction.response.defer()
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
        label="Alpine Support",
        custom_id="927077897318047854",
    )
    async def alpine_channels(self, interaction: discord.Interaction, button: discord.ui.Button):
        if button.custom_id != "927077897318047854":
            return await interaction.response.defer()
        if interaction.guild is None or interaction.guild_id != 751490725555994716:
            return await interaction.response.defer()
        guild = interaction.guild
        role = guild.get_role(int(button.custom_id))
        if role is None:
            return await interaction.response.defer()
        member = interaction.user
        if isinstance(member, discord.User):
            return await interaction.response.defer()
        if role in member.roles:
            await member.remove_roles(role)
            return await interaction.response.send_message(
                "You have been removed access from the Alpine Support Channels.",
                ephemeral=True,
            )
        await member.add_roles(role)
        return await interaction.response.send_message("You now have access to the Alpine Channels.", ephemeral=True)


class AlpineSupport(core.Cog):
    """
    Commands for Alpine Support Server
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        if ButtonRole() not in self.bot.persistent_views:
            bot.add_view(ButtonRole())
