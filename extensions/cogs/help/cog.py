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
import datetime
from typing import Optional, Mapping, List

import humanize
from difflib import get_close_matches
from discord.ext import commands, menus

import core
from utils import AvimetryBot, AvimetryContext, AvimetryPages
from .paginators import MainHelp, HelpPages, HelpSelect, CogHelp, GroupHelp


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
        cmds = await self.filter_commands(group.commands, sort=True)
        if not cmds:
            return
        # Lazy way to not show commands on the first page.
        filtered = [
            '1', '2', '3', '4', '5'
        ]
        filtered.extend(cmds)
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
                f"Can Run: {await self.can_run(command, self.context)}\n"
                f"I Need: `{self.get_perms('bot_permissions', command)}`\n"
                f"You Need: `{self.get_perms('user_permissions', command)}`"
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
        embed = discord.Embed(title="Commands", color=await self.ctx.fetch_color())
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
                    commands.Cooldown(1, 2), commands.BucketType.user
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
