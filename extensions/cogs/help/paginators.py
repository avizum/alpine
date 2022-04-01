from __future__ import annotations

from typing import List, TYPE_CHECKING

import discord
from discord.ext import commands, menus

import core
from core import Context
from utils import Paginator


if TYPE_CHECKING:
    from .cog import AvimetryHelp


# This help command is inspired by R. Danny, When I am not lazy I might make my own
class MainHelp(menus.PageSource):
    def __init__(self, ctx: Context, help: AvimetryHelp):
        self.ctx = ctx
        self.help = help
        super().__init__()

    def is_paginating(self):
        return True

    def get_max_pages(self):
        return 4

    async def get_page(self, page_number):
        self.index = page_number
        return self

    async def format_page(self, menu: menus.Menu, page: str):
        bot = self.ctx.bot
        commands = list(bot.commands)
        embed = discord.Embed(
            title="Avimetry Help Menu", color=await self.ctx.fetch_color()
        )
        info = "\n".join(
            [
                f"[Avimetry support server]({self.ctx.bot.support})",
                f"[Invite Avimetry here]({self.ctx.bot.invite})",
                "[Vote links](https://avimetry.github.io/)",
                f"[Avimetry's source code]({self.ctx.bot.support})",
            ]
        )
        if self.index == 0:
            embed.description = (
                f"Made by {self.ctx.bot.get_user(750135653638865017)}\n"
                f"Total amount of commands: {len(commands)}\n"
                f"Amount of commands that you can use here: {len(await self.help.filter_commands(commands))}\n\n"
                f"Current Bot news:\n{self.ctx.bot.news}\n\n"
                "To get started, please select a module that you need help with."
            )
        if self.index == 1:
            embed.description = (
                "Reading command signatures:\n\n"
                "**<>** means the argument is **REQUIRED**\n"
                "**[]** means the argument is **OPTIONAL**\n"
                "**[...]** means you can have **MULTIPLE arguments**\n"
                "**Do NOT** type these when using commands.\n"
                "Have fun using Avimetry!"
            )
        if self.index == 2:
            embed.description = (
                "Command Flags:\n\n"
                "Flags will show in the help command like this:\n`flag name:` <flag description>\n"
                "To use a flag, you type the command, arguments then the flags like this:\n"
                "a.ban @avizum reason: loser dm: yes delete_days: *2*\n"
                "If you have any questions, join the support server."

            )
        if self.index == 3:
            embed.description = (
                f"You can support Avimetry by voting. Here are some links.\n{info}\n"
                f"If you need help using paginators, use `{self.ctx.prefix}help paginator`"
            )
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_footer(text=self.help.ending_note())
        return embed


class CogHelp(menus.ListPageSource):
    def __init__(
        self,
        ctx: Context,
        commands,
        cog: commands.Cog,
        help_command: "AvimetryHelp",
    ):
        super().__init__(entries=commands, per_page=5)
        self.ctx = ctx
        self.cog = cog
        self.help_command = help_command

    async def format_page(self, menu, commands):
        embed = discord.Embed(
            title=f"{self.cog.qualified_name.title()} Module",
            description=self.cog.description or "No description provided",
            color=await self.ctx.fetch_color(),
        )
        embed.set_thumbnail(url=self.ctx.bot.user.display_avatar.url)
        thing = [
            f"{command.name} - {command.short_doc or 'No help provided'}"
            for command in commands
        ]

        embed.add_field(
            name=f"Commands in {self.cog.qualified_name.title()}",
            value="\n".join(thing) or "error",
        )
        embed.set_footer(text=f"Use {self.ctx.clean_prefix}{self.ctx.invoked_with} [command|module] for more help.")
        return embed


class GroupHelp(menus.ListPageSource):
    def __init__(
        self,
        ctx: Context,
        commands,
        group: commands.Group,
        help_command: "AvimetryHelp",
    ):
        super().__init__(entries=commands, per_page=5)
        self.ctx = ctx
        self.group = group
        self.hc = help_command

    async def format_page(self, menu, commands: List[core.Command]):
        embed = discord.Embed(
            title=f"Command Group: {self.group.qualified_name.title()}",
            description=self.group.help or "No description provided",
            color=await self.ctx.fetch_color(),
        )
        embed.set_thumbnail(url=self.ctx.bot.user.display_avatar.url)

        if isinstance(commands[0], str) and isinstance(commands[-1], str):
            embed.add_field(
                name="Base command usage",
                value=f"`{self.ctx.clean_prefix}{self.group.qualified_name} {self.group.signature}`",
            )
            if self.group.aliases:
                embed.add_field(
                    name="Command Aliases",
                    value=", ".join(self.group.aliases),
                    inline=False,
                )
            embed.add_field(
                name="Required Permissions",
                value=(
                    f"Can Run: {await self.hc.can_run(self.group, self.ctx)}\n"
                    f"I Need: `{self.hc.get_perms('bot_permissions', self.group)}`\n"
                    f"You Need: `{self.hc.get_perms('member_permissions', self.group)}`"
                ),
                inline=False,
            )

            cooldown = self.hc.get_cooldown(self.group)
            if cooldown:
                embed.add_field(name="Cooldown", value=cooldown, inline=False)

        else:
            thing = [
                f"{command.name} - {command.short_doc or 'No help provided'}"
                for command in commands
            ]
            embed.add_field(
                name=f"Commands in {self.group.qualified_name.title()}",
                value="\n".join(thing),
                inline=False,
            )
        embed.set_footer(
            text=(
                f"Use {self.ctx.clean_prefix}{self.ctx.invoked_with} "
                f"{self.group.qualified_name} [subcommand] for more help on a subcommand."
            )
        )
        return embed


class HelpSelect(discord.ui.Select["HelpPages"]):
    def __init__(self, ctx: Context, hc: "AvimetryHelp", cogs: List[core.Cog]):
        self.ctx = ctx
        self.hc = hc
        self.current_module = None
        options = [
            discord.SelectOption(
                label="Home",
                description="Home page of the help command",
                emoji="\U0001f3e0",
            )
        ]
        for cog in cogs:
            options.append(
                discord.SelectOption(
                    label=cog.qualified_name,
                    description=cog.description,
                    emoji=getattr(cog, "emoji", "<:avimetry:848820318117691432>"),
                )
            )
        super().__init__(
            placeholder=f"Select a module ({len(cogs)} modules)", options=options
        )

    async def callback(self, interaction: discord.Interaction):
        cog = self.ctx.bot.get_cog(self.values[0])
        if self.current_module == cog:
            return
        if self.values[0] == "Home":
            await self.view.edit_source(MainHelp(self.ctx, self.hc), interaction)
        else:
            thing = CogHelp(
                self.ctx,
                await self.hc.filter_commands(cog.get_commands(), sort=True),
                cog,
                self.hc,
            )
            await self.view.edit_source(thing, interaction)
            self.current_module = cog


class HelpPages(Paginator):
    def __init__(
        self, source: menus.PageSource, *, ctx: Context, current_page=0
    ):
        super().__init__(
            source,
            ctx=ctx,
            delete_message_after=True,
            timeout=60,
            current_page=current_page,
        )

    async def edit_source(self, source: menus.PageSource, interaction: discord.Interaction):
        self.source = source
        self.current_page = 0
        select = [i for i in self.children if isinstance(i, discord.ui.Select)][0]
        self.clear_items()
        self.add_item(select)
        self.add_items()
        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self.get_page_kwargs(page)
        self._update(0)
        await interaction.response.edit_message(**kwargs, view=self)
