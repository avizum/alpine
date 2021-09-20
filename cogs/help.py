"""
Command to get help for the bot.
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
import humanize
import datetime
import core

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
        return 1

    async def get_page(self, page_number):
        self.index = page_number
        return self

    async def format_page(self, menu, page):
        bot = self.ctx.bot
        commands = list(bot.commands)
        embed = discord.Embed(title="Avimetry Help Menu", color=await self.ctx.determine_color())
        info = " | ".join([
            f"[Support Server]({self.ctx.bot.support})",
            f"[Invite]({self.ctx.bot.invite})",
            "[Vote](https://top.gg/bot/756257170521063444/vote)",
            f"[Source]({self.ctx.bot.support})"
        ])
        embed.description = (
            f"{info}\n"
            f"Total amount of commands: {len(commands)}\n"
            f"Amount of commands that you can use here: {len(await self.help.filter_commands(commands))}\n\n"
            "Reading command signatures\n"
            "<argument> is Required\n"
            "[argument] is Optional\n"
            "[argument...] can accept multiple\n"
            "You do not need to type these when using commands.\n\n"
            "To get started, please select a module that you need help with."
        )
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_footer(text=self.help.ending_note())
        return embed


class CogHelp(menus.ListPageSource):
    def __init__(self, ctx: AvimetryContext, commands, cog: commands.Cog, help_command: "AvimetryHelp"):
        super().__init__(entries=commands, per_page=4)
        self.ctx = ctx
        self.cog = cog
        self.help_command = help_command

    async def format_page(self, menu, commands):
        embed = discord.Embed(
            title=f"{self.cog.qualified_name.title()} Module",
            description=self.cog.description or 'No description provided',
            color=await self.ctx.determine_color()
        )
        embed.set_thumbnail(url=self.ctx.bot.user.display_avatar.url)
        thing = [
            f"{command.name} - {command.short_doc or 'No help provided'}"
            for command in commands
        ]

        embed.add_field(name=f"Commands in {self.cog.qualified_name.title()}", value="\n".join(thing) or 'error')
        embed.set_footer(text=self.help_command.ending_note())
        return embed


class GroupHelp(menus.ListPageSource):
    def __init__(self, ctx: AvimetryContext, commands, group: commands.Group, help_command: "AvimetryHelp"):
        super().__init__(entries=commands, per_page=4)
        self.ctx = ctx
        self.group = group
        self.hc = help_command

    async def format_page(self, menu, commands):
        embed = discord.Embed(
            title=f"Command Group: {self.group.qualified_name.title()}",
            description=self.group.help or 'No description provided',
            color=await self.ctx.determine_color(),
        )
        embed.add_field(
            name="Base command usage",
            value=f"`{self.ctx.clean_prefix}{self.group.qualified_name} {self.group.signature}`")
        if self.group.aliases:
            embed.add_field(
                name="Command Aliases",
                value=", ".join(self.group.aliases),
                inline=False)
        embed.add_field(
            name="Required Permissions",
            value=(
                f"Can Use: {await self.hc.can_run(self.group, self.ctx)}\n"
                f"Bot Permissions: `{self.hc.get_perms('bot_permissions', self.group)}`\n"
                f"User Permissions: `{self.hc.get_perms('user_permissions', self.group)}`"
            ),
            inline=False)

        cooldown = self.hc.get_cooldown(self.group)
        if cooldown:
            embed.add_field(
                name="Cooldown",
                value=cooldown,
                inline=False)

        embed.set_thumbnail(url=self.ctx.bot.user.display_avatar.url)
        thing = [
            f"{command.name} - {command.short_doc or 'No help provided'}"
            for command in commands
        ]

        embed.add_field(
            name=f"Commands in {self.group.qualified_name.title()}",
            value="\n".join(thing),
            inline=False
        )
        embed.set_footer(text=self.hc.ending_note())
        return embed


class HelpSelect(discord.ui.Select):
    def __init__(self, ctx: AvimetryContext, hc, cogs: list[core.Cog]):
        self.ctx = ctx
        self.hc = hc
        self.current_module = None
        options = [discord.SelectOption(label="Home", description="Home page of the help command", emoji="\U0001f3e0")]
        for cog in cogs:
            options.append(
                discord.SelectOption(
                    label=cog.qualified_name,
                    description=cog.description,
                    emoji=getattr(cog, "emoji", "<:avimetry:848820318117691432>")
                )
            )
        super().__init__(
            placeholder="Select a module...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        cog = self.ctx.bot.get_cog(self.values[0])
        if self.current_module == cog:
            return
        elif self.values[0] == "Home":
            await self.view.edit_source(MainHelp(self.ctx, self.hc), interaction)
        else:
            thing = CogHelp(self.ctx, cog.get_commands(), cog, self.hc)
            await self.view.edit_source(thing, interaction)
            self.current_module = cog


class HelpPages(AvimetryPages):
    def __init__(self, source: menus.PageSource, *, ctx: AvimetryContext):
        super().__init__(source, ctx=ctx, remove_view_after=True)

    def _update(self):
        if self.show_page_number.emoji:
            self.show_page_number.emoji = None
        current = self.current_page + 1
        last = self.source.get_max_pages()
        self.show_page_number.label = f"Page {current}/{last}"

    async def edit_source(self, source, interaction):
        self.source = source
        self.current_page = 0
        select = [i for i in self.children if isinstance(i, discord.ui.Select)][0]
        self.clear_items()
        self.add_item(select)
        self.add_items()
        await self.source._prepare_once()
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self._update()
        await interaction.response.edit_message(**kwargs, view=self)


class AvimetryHelp(commands.HelpCommand):
    def get_perms(self, perm_type: str, command: commands.Command):
        permissions = getattr(command, perm_type, None) or command.extras.get(perm_type, ['send_messages'])
        return ", ".join(permissions).replace("_", " ").replace("guild", "server").title()

    async def can_run(self, command, ctx):
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
            time = "time"
            if rate > 1:
                time = "times"
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

    async def send_error_message(self, error):
        embed = discord.Embed(
            title="Help Error", description=error, color=discord.Color.red()
        )
        embed.set_footer(text=self.ending_note())
        await self.get_destination().send(embed=embed)

    def get_destination(self):
        return self.context

    async def send_bot_help(self, mapping):
        items = []
        for cog in mapping:
            if not cog:
                continue
            filtered = await self.filter_commands(cog.get_commands())
            if filtered:
                items.append(cog)
        items.sort(key=lambda c: c.qualified_name)
        menu = HelpPages(MainHelp(self.context, self), ctx=self.context)
        menu.clear_items()
        menu.add_item(HelpSelect(self.context, self, items))
        menu.add_items()
        await menu.start()

    async def send_cog_help(self, cog: commands.Cog):
        filtered = await self.filter_commands(cog.get_commands(), sort=False)
        if not filtered:
            return
        menu = HelpPages(CogHelp(self.context, filtered, cog, self), ctx=self.context)
        await menu.start()

    async def send_group_help(self, group):
        filtered = await self.filter_commands(group.commands, sort=False)
        if not filtered:
            return
        menu = HelpPages(GroupHelp(self.context, filtered, group, self), ctx=self.context)
        await menu.start()

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(
            title=f"Command: {command.qualified_name}")

        embed.add_field(
            name="Command Usage",
            value=f"`{self.context.clean_prefix}{command.qualified_name} {command.signature}`")
        if command.aliases:
            embed.add_field(
                name="Command Aliases",
                value=", ".join(command.aliases),
                inline=False)
        embed.add_field(
            name="Description",
            value=command.help or "No help was provided.",
            inline=False)
        embed.add_field(
            name="Required Permissions",
            value=(
                f"Can Use: {await self.can_run(command, self.context)}\n"
                f"Bot Permissions: `{self.get_perms('bot_perms', command)}`\n"
                f"User Permissions: `{self.get_perms('user_permissions', command)}`"),
            inline=False)
        cooldown = self.get_cooldown(command)
        if cooldown:
            embed.add_field(
                name="Cooldown",
                value=cooldown)
        embed.set_thumbnail(url=str(self.context.bot.user.display_avatar.url))
        embed.set_footer(text=self.ending_note())
        await self.get_destination().send(embed=embed)

    async def command_not_found(self, string):
        all_commands = []
        for cmd in self.context.bot.commands:
            try:
                await cmd.can_run(self.context)
                all_commands.append(cmd.name)
                if cmd.aliases:
                    all_commands.extend(cmd.aliases)
            except commands.CommandError:
                continue
        match = "\n".join(get_close_matches(string, all_commands))
        if match:
            return f'"{string}" is not a command or module. Did you mean...\n`{match}`'
        return f'"{string}" is not a command or module. I couln\'t find any similar commands.'

    async def subcommand_not_found(self, command, string):
        return f'"{string}" is not a subcommand of "{command}".'


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
                checks=[core.bot_has_permissions(add_reactions=True).predicate],
                cooldown=commands.CooldownMapping(commands.Cooldown(10, 30), commands.BucketType.user)
            )
        )
        help_command.cog = self
        self.bot.help_command = help_command

    def cog_unload(self):
        self.bot.help_command = self.default


def setup(bot):
    bot.add_cog(HelpCommand(bot))
