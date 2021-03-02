import discord
from discord.ext import commands
import os
import pathlib
from difflib import get_close_matches
import traceback
import humanize


class HelpEmbeded(commands.HelpCommand):
    def get_files(self):
        total = 0
        file_amount = 0
        ENV = "env"
        for path, _, files in os.walk("."):
            for name in files:
                file_dir = str(pathlib.PurePath(path, name))
                if not name.endswith(".py") or ENV in file_dir:
                    continue
                file_amount += 1
                with open(file_dir, "r", encoding="utf-8") as file:
                    for line in file:
                        if not line.strip().startswith("#") or not line.strip():
                            total += 1
        return f"is a bot that is spread out across **{file_amount}** python files, with a total of **{total}** lines of code."

    async def get_bot_perms(self, command):
        user_perms = []
        try:
            check = command.checks[1]
            await check(1)
        except Exception as e:
            frames = [*traceback.walk_tb(e.__traceback__)]
            last_trace = frames[-1]
            frame = last_trace[0]
            try:
                for i in frame.f_locals['perms']:
                    user_perms.append(i)
                return "\n".join(user_perms)
            except KeyError:
                return None

    async def get_user_perms(self, command):
        user_perms = []
        try:
            check = command.checks[0]
            await check(0)
        except Exception as e:
            frames = [*traceback.walk_tb(e.__traceback__)]
            last_trace = frames[-1]
            frame = last_trace[0]
            try:
                for i in frame.f_locals['perms']:
                    user_perms.append(i)
                return "\n".join(user_perms)
            except KeyError:
                return None

    def get_cooldown(self, command):
        try:
            rate = command._buckets._cooldown.rate
            per = humanize.precisedelta(command._buckets._cooldown.per)
            time = "time"
            if rate > 1:
                time = "times"
            return f"{per} every {rate} {time}"
        except Exception:
            return None

    def gending_note(self):
        return "Use {0}{1} [command] or [module] for more info on a command or module.".format(
            self.clean_prefix, self.invoked_with
        )

    def bnote(self):
        return "<argument> = required argument\n[argument] = optional argument\n[argument...] = accepts multiple arguments"

    def gcommand_signature(self, command):
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            name_alias = f'{command.name} | {" | ".join(command.aliases)}'
            if parent:
                name_alias = f"{parent} {name_alias}"
            alias = name_alias
        else:
            alias = command.name if not parent else f"{parent} {command.name}"
        return f"{alias} {command.signature}"

    async def send_error_message(self, error):
        embed = discord.Embed(
            title="Help Menu", description=error, color=discord.Color.red()
        )
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    def get_destination(self):
        return self.context

    async def send_bot_help(self, mapping):
        det_prefix = self.clean_prefix
        if det_prefix == f"@{self.context.bot.user.display_name} ":
            det_prefix = f"`@{self.context.bot.user.display_name} `"
        else:
            det_prefix = f"`{self.clean_prefix}` or `@{self.context.bot.user.display_name} `"
        embed = discord.Embed(
            title="Help Menu",
            description=(
                f"{self.context.bot.user.name} {self.get_files()}\n\n```{self.bnote()}```\n"
                "Do not put the brackets with the command. It is not needed.\n\n"
                f"The prefix for **{self.get_destination().guild.name}** is {det_prefix}"
            ),
        )
        modules_list = []
        for cog, command in mapping.items():
            name = "No Category" if cog is None else cog.qualified_name.title()
            filtered = await self.filter_commands(command, sort=True)
            if filtered:
                modules_list.append(f"{name} ({len(command)})")
        embed.add_field(
            name="Modules", value="{}".format("\n".join(modules_list)), inline=True
        )
        embed.add_field(
            name="Credits",
            value=(
                "ZaneAPI\n"
                "Some Random API"
            )
        )
        embed.set_thumbnail(url=str(self.context.bot.user.avatar_url))
        embed.set_footer(text=f"Use {self.clean_prefix}{self.invoked_with} [module] to get info on a module.")
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(
            title=f"{cog.qualified_name.title()} Commands",
            description=cog.description or "No module description",
        )
        if cog.description:
            embed.description = cog.description
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        command_list = []
        for command in filtered:
            command_list.append(command.name)
        embed.add_field(
            name=f"Commands in {cog.qualified_name.title()}",
            value="\n".join(command_list),
            inline=False,
        )
        embed.set_thumbnail(url=str(self.context.bot.user.avatar_url))
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(
            title=f"Commands in group {group.qualified_name.title()}",
            description=f"{group.short_doc}",
        )
        embed.add_field(
            name="Base command usage",
            value=f"`{self.clean_prefix}{group.qualified_name}`"
        )
        embed.add_field(
            name="Command Aliases",
            value=", ".join(group.aliases) or None,
            inline=False
        )
        embed.add_field(
            name="Required Permissions",
            value=(
                f"Bot Permissions: `{await self.get_bot_perms(group)}`\n"
                f"User Permissions: `{await self.get_user_perms(group)}`"
            ),
            inline=False
        )
        embed.add_field(
            name="Cooldown",
            value=self.get_cooldown(group)
        )

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            group_commands = []
            for command in filtered:
                group_commands.append(command.name)
            embed.add_field(
                name=f"Subcommands for {group.qualified_name}",
                value="\n".join(group_commands) or None,
                inline=False,
            )
        embed.set_thumbnail(url=str(self.context.bot.user.avatar_url))
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title="Command: {0.qualified_name}".format(command),
        )

        embed.add_field(
            name="Command Usage",
            value=f"`{self.clean_prefix}{command.name} {command.signature}`"
        )
        embed.add_field(
            name="Command Aliases",
            value=", ".join(command.aliases) or None,
            inline=False
        )
        usage = command.short_doc
        if not usage:
            usage = "No description provided, now go try doing it yourself"
        embed.add_field(
            name="Description",
            value=usage,
            inline=True,
        )

        embed.add_field(
            name="Required Permissions",
            value=(
                f"Bot Permissions: `{await self.get_bot_perms(command)}`\n"
                f"User Permissions: `{await self.get_user_perms(command)}`"
            ),
            inline=False
        )
        embed.add_field(
            name="Cooldown",
            value=self.get_cooldown(command)
        )
        embed.set_thumbnail(url=str(self.context.bot.user.avatar_url))
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    async def command_not_found(self, string):
        lol = "\n".join(
            get_close_matches(string, [i.name for i in self.context.bot.commands])
        )
        if lol:
            return f'"{string}" is not a command/module. Did you mean...\n`{lol}`'
        if not lol:
            return f'"{string}" is not a command/module and I couln\'t find any similar commands.'

    async def subcommand_not_found(self, command, string):
        return '"{0}" is not a subcommand of "{1}".'.format(string, command)


class Help(commands.Cog):
    def __init__(self, avimetry):
        self.HCne = avimetry.help_command
        self.avimetry = avimetry
        self.avimetry.help_command = HelpEmbeded(
            command_attrs=dict(
                hidden=True,
                aliases=["halp", "helps", "hlp"],
                brief="Why do you need help with the help command? Oh well, Here it is anyways",
                usage="[command] or [module]",
            )
        )

    def cog_unload(self):
        self.avimetry.help_command = self.HCne


def setup(avimetry):
    avimetry.add_cog(Help(avimetry))
