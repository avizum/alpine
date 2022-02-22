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

from utils.paginators import OldAvimetryPages
import discord
import humanize
import datetime
import core

from discord.ext import commands, menus
from difflib import get_close_matches
from core import Bot, Context
from utils import Paginator


class MainHelp(menus.ListPageSource):
    def __init__(self, ctx: Context, mapping, help_command: "AvimetryHelp"):
        super().__init__(entries=mapping, per_page=4)
        self.ctx = ctx
        self.mapping = mapping
        self.help_command = help_command

    async def format_page(self, menu, modules):
        bot = self.ctx.bot
        command = list(bot.commands)
        usable = (
            f"Total Commands: {len(command)} | "
            f"Usable by you here: {len(await self.help_command.filter_commands(command))}"
        )
        info = [
            f"[Support Server]({self.ctx.bot.support})",
            f"[Invite]({self.ctx.bot.invite})",
            "[Vote](https://top.gg/bot/756257170521063444/vote)",
            f"[Source]({self.ctx.bot.support})",
        ]
        embed = discord.Embed(
            title=f"Avimetry {self.help_command.invoked_with.title()} Menu",
            description=(
                f"{self.help_command.command_signature()}\n"
                f"{usable}\n{' | '.join(info)}"
            ),
            color=await self.ctx.fetch_color(),
        )
        embed.add_field(name="Modules", value="\n".join(modules))
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        embed.set_footer(
            icon_url=self.ctx.author.display_avatar.url,
            text=(
                f"{self.help_command.ending_note()} | "
                f"Page {menu.current_page+1}/{self.get_max_pages()} ({len(self.mapping)} Modules)"
            ),
        )
        return embed


class CogHelp(menus.ListPageSource):
    def __init__(
        self,
        ctx: Context,
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
        if self.get_max_pages() != 1:
            embed.set_footer(
                text=f"Page {menu.current_page+1}/{self.get_max_pages()} ({len(self.cog.get_commands())} Commands)"
            )
        else:
            embed.set_footer(text=self.help_command.ending_note())
        return embed


class GroupHelp(menus.ListPageSource):
    def __init__(
        self,
        ctx: Context,
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
            color=await self.ctx.fetch_color(),
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
                f"User Permissions: `{self.hc.get_perms('member_permissions', self.group)}`"
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
        if self.get_max_pages() != 1:
            embed.set_footer(
                text=f"Page {menu.current_page+1}/{self.get_max_pages()} ({len(self.group.commands)} Commands)"
            )
        else:
            embed.set_footer(text=self.hc.ending_note())
        return embed


class AvimetryHelp(commands.HelpCommand):
    def get_perms(self, perm_type: str, command: commands.Command):
        permissions = getattr(command, perm_type, None) or command.extras.get(
            perm_type, ["send_messages"]
        )
        return (
            ", ".join(permissions).replace("_", " ").replace("guild", "server").title()
        )

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
        emoji_map = {
            "animals": "\U0001f98a Animals",
            "fun": "\U0001f3b1 Fun",
            "games": "\U0001f3ae Games",
            "images": "\U0001f4f7 Images",
            "moderation": "\U0001f52b Moderation",
            "settings": "\U00002699 Settings",
            "music": "\U0001f3b5 Music",
            "bot info": "\U00002139 Bot Info",
        }
        items = []
        for cog in mapping:
            if not cog:
                continue
            filtered = await self.filter_commands(cog.get_commands())
            if filtered:
                items.append(cog)
        items.sort(key=lambda c: c.qualified_name)
        cogs = []
        for cog in items:
            try:
                thing = f"{emoji_map[cog.qualified_name.lower()]} - {cog.description or 'No description'}"
            except KeyError:
                thing = f"<:avimetry:848820318117691432> {cog.qualified_name} - {cog.description or 'No description'}"
            cogs.append(thing)
        menu = OldAvimetryPages(MainHelp(self.context, cogs, self))
        await menu.start(self.context)

    async def send_cog_help(self, cog: commands.Cog):
        filtered = await self.filter_commands(cog.get_commands(), sort=False)
        if not filtered:
            return
        menu = Paginator(CogHelp(self.context, filtered, cog, self))
        await menu.start(self.context)

    async def send_group_help(self, group):
        filtered = await self.filter_commands(group.commands, sort=False)
        if not filtered:
            return
        menu = Paginator(GroupHelp(self.context, filtered, group, self))
        await menu.start(self.context)

    async def send_command_help(self, command: commands.Command):
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
                f"Bot Permissions: `{self.get_perms('bot_perms', command)}`\n"
                f"User Permissions: `{self.get_perms('member_permissions', command)}`"
            ),
            inline=False,
        )
        cooldown = self.get_cooldown(command)
        if cooldown:
            embed.add_field(name="Cooldown", value=cooldown)
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
    def __init__(self, bot: Bot):
        self.default = bot.help_command
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        help_command = AvimetryHelp(
            verify_checks=False,
            show_hidden=False,
            command_attrs=dict(
                hidden=True,
                aliases=["halp", "helps", "hlp", "hlep", "hep"],
                usage="[command|module]",
                checks=[core.bot_has_permissions(add_reactions=True).predicate],
                cooldown=commands.CooldownMapping(
                    commands.Cooldown(10, 30), commands.BucketType.user
                ),
            ),
        )
        help_command.cog = self
        self.bot.help_command = help_command

    def cog_unload(self):
        self.bot.help_command = self.default


def setup(bot):
    bot.add_cog(HelpCommand(bot))
