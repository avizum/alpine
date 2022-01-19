"""
Command to get help for the bot.
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
import humanize
import datetime
import core

from typing import Optional, Mapping, List
from discord.ext import commands, menus
from difflib import get_close_matches
from utils import AvimetryBot, AvimetryContext, AvimetryPages


# This help command is inspired by R. Danny, When I am not lazy I might make my own
class MainHelp(menus.PageSource):
    def __init__(self, ctx: AvimetryContext, help: "AvimetryHelp"):
        self.ctx = ctx
        self.help = help
        super().__init__()

    def is_paginating(self):
        return True

    def get_max_pages(self):
        return 3

    async def get_page(self, page_number):
        self.index = page_number
        return self

    async def format_page(self, menu: menus.Menu, page: str):
        bot = self.ctx.bot
        commands = list(bot.commands)
        embed = discord.Embed(
            title="Avimetry Help Menu", color=await self.ctx.determine_color()
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
                f"Total amount of commands: {len(commands)}\n"
                f"Amount of commands that you can use here: {len(await self.help.filter_commands(commands))}\n\n"
                f"Current Bot news:\n{self.ctx.bot.news}\n\n"
                "To get started, please select a module that you need help with."
            )
        if self.index == 1:
            embed.description = (
                "Reading command signatures:\n\n"
                "**<>** means the argument is REQUIRED\n"
                "**[]** means the argument is OPTIONAL\n"
                "**[...]** means you can have MULTIPLE arguments\n"
                "Do NOT type these when writing your command.\n"
                "Have fun using Avimetry!"
            )
        if self.index == 2:
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
        ctx: AvimetryContext,
        commands,
        cog: commands.Cog,
        help_command: "AvimetryHelp",
    ):
        super().__init__(entries=commands, per_page=4)
        self.ctx = ctx
        self.cog = cog
        self.help_command = help_command

    async def format_page(self, menu, commands):
        embed = discord.Embed(
            title=f"{self.cog.qualified_name.title()} Module",
            description=self.cog.description or "No description provided",
            color=await self.ctx.determine_color(),
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
        embed.set_footer(text=self.help_command.ending_note())
        return embed


class GroupHelp(menus.ListPageSource):
    def __init__(
        self,
        ctx: AvimetryContext,
        commands,
        group: commands.Group,
        help_command: "AvimetryHelp",
    ):
        super().__init__(entries=commands, per_page=4)
        self.ctx = ctx
        self.group = group
        self.hc = help_command

    async def format_page(self, menu, commands):
        embed = discord.Embed(
            title=f"Command Group: {self.group.qualified_name.title()}",
            description=self.group.help or "No description provided",
            color=await self.ctx.determine_color(),
        )
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
                f"Can Use: {await self.hc.can_run(self.group, self.ctx)}\n"
                f"Bot Permissions: `{self.hc.get_perms('bot_permissions', self.group)}`\n"
                f"User Permissions: `{self.hc.get_perms('user_permissions', self.group)}`"
            ),
            inline=False,
        )

        cooldown = self.hc.get_cooldown(self.group)
        if cooldown:
            embed.add_field(name="Cooldown", value=cooldown, inline=False)

        embed.set_thumbnail(url=self.ctx.bot.user.display_avatar.url)
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


class HelpSelect(discord.ui.Select):
    def __init__(self, ctx: AvimetryContext, hc: "AvimetryHelp", cogs: List[core.Cog]):
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


class HelpPages(AvimetryPages):
    def __init__(
        self, source: menus.PageSource, *, ctx: AvimetryContext, current_page=0
    ):
        super().__init__(
            source,
            ctx=ctx,
            delete_message_after=True,
            timeout=45,
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


class AvimetryHelp(commands.HelpCommand):
    def get_perms(self, perm_type: str, command: commands.Command):
        permissions = getattr(command, perm_type, None) or command.extras.get(
            perm_type, ["send_messages"]
        )
        return (
            ", ".join(permissions).replace("_", " ").replace("guild", "server").title()
        )

    async def can_run(self, command: core.Command, ctx: AvimetryContext):
        try:
            await command.can_run(ctx)
            emoji = ctx.bot.emoji_dictionary["green_tick"]
        except commands.CommandError:
            emoji = ctx.bot.emoji_dictionary["red_tick"]
        return emoji

    def get_cooldown(self, command):
        try:
            rate = command._buckets._cooldown.rate
            cd_type = command._buckets.type.name
            per = humanize.precisedelta(command._buckets._cooldown.per)
            time = "times" if rate > 1 else "time"
            return f"{per} every {rate} {time} per {cd_type}"
        except AttributeError:
            return None

    def ending_note(self):
        return f"Use {self.context.clean_prefix}{self.invoked_with} [command|module] for more help."

    def command_signature(self):
        return (
            "```<> is a required argument\n"
            "[] is an optional argument\n"
            "[...] accepts multiple arguments```"
        )

    async def send_error_message(self, _):
        pass

    async def on_help_command_error(self, ctx, error):
        ctx.bot.dispatch("command_error", ctx, error)

    async def filter_cogs(self, mapping: Mapping[Optional[core.Cog], List[core.Command]] = None):
        mapping = mapping or self.get_bot_mapping()
        items = []
        for cog in mapping:
            if not cog:
                continue
            filtered = await self.filter_commands(cog.get_commands(), sort=True)
            if filtered:
                items.append(cog)
        items.sort(key=lambda c: c.qualified_name)
        return items

    async def send_bot_help(self, mapping: Mapping[Optional[core.Cog], List[core.Command]]):
        items = await self.filter_cogs(mapping)
        source = MainHelp(self.context, self)
        menu = HelpPages(source, ctx=self.context)
        menu.clear_items()
        menu.add_item(HelpSelect(self.context, self, items))
        menu.add_items()
        await menu.start()

    async def send_cog_help(self, cog: core.Cog):
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if not filtered:
            return
        items = await self.filter_cogs()
        menu = HelpPages(CogHelp(self.context, filtered, cog, self), ctx=self.context)
        menu.clear_items()
        menu.add_item(HelpSelect(self.context, self, items))
        menu.add_items()
        await menu.start()

    async def send_group_help(self, group: core.Group):
        filtered = await self.filter_commands(group.commands, sort=True)
        if not filtered:
            return
        menu = HelpPages(
            GroupHelp(self.context, filtered, group, self), ctx=self.context
        )
        await menu.start()

    async def send_command_help(self, command: core.Command):
        embed = discord.Embed(title=f"Command: {command.qualified_name}")

        embed.add_field(
            name="Command Usage",
            value=f"`{self.context.clean_prefix}{command.qualified_name} {command.signature}`",
        )
        if command.aliases:
            embed.add_field(
                name="Command Aliases", value=", ".join(command.aliases), inline=False
            )
        embed.add_field(
            name="Description",
            value=command.help or "No help was provided.",
            inline=False,
        )
        embed.add_field(
            name="Required Permissions",
            value=(
                f"Can Use: {await self.can_run(command, self.context)}\n"
                f"Bot Permissions: `{self.get_perms('bot_permissions', command)}`\n"
                f"User Permissions: `{self.get_perms('user_permissions', command)}`"
            ),
            inline=False,
        )
        cooldown = self.get_cooldown(command)
        if cooldown:
            embed.add_field(name="Cooldown", value=cooldown)
        embed.set_thumbnail(url=str(self.context.bot.user.display_avatar.url))
        embed.set_footer(text=self.ending_note())
        await self.context.send(embed=embed)

    async def command_not_found(self, string: str):
        all_commands = []
        for cmd in self.context.bot.commands:
            try:
                await cmd.can_run(self.context)
                all_commands.append(cmd.name)
                if cmd.aliases:
                    all_commands.extend(cmd.aliases)
            except commands.CommandError:
                continue
        match = get_close_matches(string, all_commands)
        if match:
            embed = discord.Embed(
                title="Command not found",
                description=f'"{string}" is not a command or module. Did you mean {match[0]}?',
            )
            conf = await self.context.confirm(embed=embed)
            if conf.result:
                self.context.message._edited_timestamp = datetime.datetime.now(
                    datetime.timezone.utc
                )
                return await self.send_command_help(
                    self.context.bot.get_command(match[0])
                )
            return await conf.message.delete()
        return await self.context.send("Command not found.")

    async def subcommand_not_found(self, command, string):
        return await self.context.send(
            f'"{string}" is not a subcommand of "{command}".'
        )


class AllCommandsPageSource(menus.ListPageSource):
    def __init__(self, commands: List[commands.Command], ctx: AvimetryContext):
        self.ctx = ctx
        super().__init__(commands, per_page=4)

    async def format_page(self, menu: menus.Menu, page: core.Command):
        embed = discord.Embed(title="Commands", color=await self.ctx.determine_color())
        for i in page:
            embed.add_field(name=i.qualified_name, value=i.help, inline=False)
        return embed


class HelpCommand(core.Cog):
    def __init__(self, bot: AvimetryBot):
        self.default = bot.help_command
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        help_command = AvimetryHelp(
            verify_checks=False,
            show_hidden=False,
            command_attrs=dict(
                hidden=True,
                usage="[command|module]",
                aliases=["h"],
                cooldown=commands.CooldownMapping(
                    commands.Cooldown(1, 3), commands.BucketType.user
                ),
            ),
        )
        help_command.cog = self
        self.bot.help_command = help_command

    @core.command(hidden=True)
    async def allcommands(self, ctx: AvimetryContext):
        """
        A list of all commands.
        """
        menu = AvimetryPages(
            AllCommandsPageSource(list(self.bot.commands), ctx),
            ctx=ctx,
            remove_view_after=True,
        )
        await menu.start()

    def cog_unload(self):
        self.bot.help_command = self.default


def setup(bot: AvimetryBot):
    bot.add_cog(HelpCommand(bot))
