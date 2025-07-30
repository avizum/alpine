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

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

import core

from .views import ConfirmNewSettingsMenu, SettingsView

if TYPE_CHECKING:
    from core import Bot, Context


class Settings(core.GroupCog, group_name="settings"):
    """Configure server and user settings."""

    def __init__(self, bot: Bot) -> None:
        self.emoji = "\U00002699"
        self._settings: dict[int, SettingsView] = {}
        super().__init__(bot)

    async def cog_check(self, ctx: Context) -> bool:
        if self._settings.get(ctx.guild.id):
            raise commands.MaxConcurrencyReached(1, commands.BucketType.guild)
        return True

    async def cog_command_error(self, ctx: Context, error: Exception):
        if isinstance(error, commands.MaxConcurrencyReached):
            ctx.locally_handled = True
            settings_view = self._settings[ctx.guild.id]
            view = ConfirmNewSettingsMenu(menu=settings_view, ctx=ctx, cog=self)
            await ctx.send("A settings menu is already open.", view=view, ephemeral=True)
            return

    @core.command(hybrid=True, app_command_name="show")
    @core.has_permissions(manage_guild=True)
    async def settings(self, ctx: Context):
        """
        Configure Alpine settings for this server.
        """
        guild_settings = await ctx.database.get_or_fetch_guild(ctx.guild.id)
        view = SettingsView(ctx, self, guild_settings)
        await view.start()

    @core.command(hybrid=True)
    @core.has_permissions(manage_guild=True)
    async def prefix(self, ctx: Context):
        """Show custom prefix configuration."""
        guild_settings = await ctx.database.get_or_fetch_guild(ctx.guild.id)
        view = SettingsView(ctx, self, guild_settings)
        return await view.start(container=1)

    @core.command(hybrid=True)
    @core.has_permissions(manage_guild=True)
    async def logging(self, ctx: Context):
        """Configure logging."""
        guild_settings = await ctx.database.get_or_fetch_guild(ctx.guild.id)
        view = SettingsView(ctx, self, guild_settings)
        return await view.start(container=2)

    @core.command(name="joins-and-leaves", aliases=["joinsandleaves", "jal", "joins", "leaves"], hybrid=True)
    @core.has_permissions(manage_guild=True)
    async def joins_and_leaves(self, ctx: Context):
        """Configure join and leave messages."""
        guild_settings = await ctx.database.get_or_fetch_guild(ctx.guild.id)
        view = SettingsView(ctx, self, guild_settings)
        return await view.start(container=3)

    @core.command(hybrid=True)
    @core.has_permissions(manage_guild=True)
    @core.bot_has_permissions(manage_channels=True, manage_roles=True, manage_messages=True)
    async def verification(self, ctx: Context):
        """Configure member verification."""
        guild_settings = await ctx.database.get_or_fetch_guild(ctx.guild.id)
        view = SettingsView(ctx, self, guild_settings)
        return await view.start(container=4)

    @core.command(hybrid=True, name="commands")
    @core.has_permissions(manage_guild=True)
    @core.bot_has_permissions(manage_channels=True, manage_roles=True, manage_messages=True)
    async def _commands(self, ctx: Context):
        """Configure commands for the server."""
        guild_settings = await ctx.database.get_or_fetch_guild(ctx.guild.id)
        view = SettingsView(ctx, self, guild_settings)
        return await view.start(container=5)

    @core.group(invoke_without_command=True, case_insensitive=True, hybrid=True)
    @core.cooldown(1, 60, commands.BucketType.user)
    async def theme(self, ctx: Context, *, color: discord.Color):
        """Set your theme.

        This color will be used for embeds sent by the bot.
        """

        user_data = await ctx.database.get_or_fetch_user(ctx.author.id)
        embed = discord.Embed(description="Does this look good?", color=color)
        conf = await ctx.confirm(embed=embed)
        if conf.result:
            await user_data.update(color=color.value)
            return await conf.message.edit(content=f"Set theme to {color}", embed=None)
        return await conf.message.edit(content="Okay, nevermind.", embed=None)

    @theme.command(aliases=["none", "no", "not", "gone"])
    async def remove(self, ctx: Context):
        """Remove your theme.

        This will remove the color used for embeds and will use your top role color instead.
        """
        user_data = ctx.database.get_user(ctx.author.id)
        if not user_data:
            return await ctx.send("You do not have a theme set.")
        conf = await ctx.confirm(message="Are you sure you want to remove your theme?")
        if conf.result:
            await user_data.update(color=0)
            return await conf.message.edit(content="Your theme was removed.")
        return await conf.message.edit(content="Okay, nevermind.")

    @theme.command()
    async def random(self, ctx: Context):
        """Set a random theme.

        This will pick a random color for embeds.
        """
        user_data = await ctx.database.get_or_fetch_user(ctx.author.id)
        color = discord.Color.random()
        await user_data.update(color=color.value)
        embed = discord.Embed(description=f"Set your theme to {color}", color=color)
        return await ctx.send(embed=embed)

    @theme.command()
    async def view(self, ctx: Context):
        """Show your current theme preview."""
        embed = discord.Embed(title="Preview", description="This is how your embeds will look like.")
        await ctx.send(embed=embed)

    @core.command(hidden=True)
    async def getowner(self, ctx: Context):
        """
        Command for me to get bot owner if I somehow lose it.
        """
        if ctx.author.id != 750135653638865017:
            self.bot.owner_id = None
            self.bot.owner_ids = set()
