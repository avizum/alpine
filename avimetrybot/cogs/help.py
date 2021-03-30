import discord
from discord.ext import commands
from difflib import get_close_matches
import traceback
import humanize


class HelpEmbeded(commands.HelpCommand):
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
                return ", ".join(user_perms).replace("_", " ").title()
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
                return ", ".join(user_perms).replace("_", " ").title()
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
        return "Use {0}{1} [command|module] for help on a command or module.".format(
            self.clean_prefix, self.invoked_with
        )

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
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    def get_destination(self):
        return self.context

    async def send_bot_help(self, mapping):
        prefixes = await self.context.cache.get_guild_settings(self.context.guild.id)
        determine_prefix = f"`{'` | `'.join(prefixes['prefixes'])}`"
        embed = discord.Embed(
            title="Help Menu",
            description=(
                f"{self.command_signature()}\nDo not put the brackets with the commands.\n"
                f"Here are the prefixes for **{self.get_destination().guild.name}**.\n{determine_prefix}\n"
            ),
        )
        modules_list = []
        for cog, command in mapping.items():
            name = "No Category" if cog is None else cog.qualified_name
            filtered = await self.filter_commands(command, sort=True)
            if filtered:
                modules_list.append(f"{name}")
        embed.add_field(
            name="Modules", value="{}".format("\n".join(modules_list)), inline=True
        )
        embed.set_thumbnail(url=str(self.context.bot.user.avatar_url))
        embed.set_footer(text=f"Use {self.clean_prefix}{self.invoked_with} [module|command] to get info on a module.")
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(
            title=f"{cog.qualified_name.title()} Commands",
            description=cog.description or "No description was provided",
        )
        if cog.description:
            embed.description = cog.description
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        command_list = []
        for command in filtered:
            command_list.append(command.name)
        split_list = [command_list[i:i+3]for i in range(0, len(command_list), 3)]
        value = []
        for lists in split_list:
            value.append(", ".join(lists))

        embed.add_field(
            name=f"Commands in {cog.qualified_name.title()}",
            value='{}'.format(",\n".join(value)) or None,
            inline=False,
        )
        embed.set_thumbnail(url=str(self.context.bot.user.avatar_url))
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(
            title=f"Commands in group {group.qualified_name.title()}",
            description=f"{group.short_doc}" or None,
        )
        embed.add_field(
            name="Base command usage",
            value=(
                f"`{self.clean_prefix}{group.qualified_name} {group.signature}`"
            )
        )
        embed.add_field(
            name="Command Aliases",
            value=", ".join(group.aliases) or None,
            inline=False
        )
        try:
            can_run_check = await group.can_run(self.context)
            if can_run_check:
                can_run = self.context.bot.emoji_dictionary["green_tick"]
            else:
                can_run = self.context.bot.emoji_dictionary["red_tick"]
        except commands.CommandError:
            can_run = self.context.bot.emoji_dictionary["red_tick"]
        embed.add_field(
            name="Required Permissions",
            value=(
                f"Can Use: {can_run}\n"
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
            split_list = [group_commands[i:i+3]for i in range(0, len(group_commands), 3)]
            value = []
            for lists in split_list:
                value.append(", ".join(lists))

            embed.add_field(
                name=f"Subcommands for {group.qualified_name}",
                value='{}'.format(",\n".join(value)) or None,
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
            value=(
                f"`{self.clean_prefix}{command.name} {command.signature}`"
                )
        )
        embed.add_field(
            name="Command Aliases",
            value=", ".join(command.aliases) or None,
            inline=False
        )
        embed.add_field(
            name="Description",
            value=command.short_doc or None,
            inline=True,
        )
        try:
            can_run_check = await command.can_run(self.context)
            if can_run_check:
                can_run = self.context.bot.emoji_dictionary["green_tick"]
            else:
                can_run = self.context.bot.emoji_dictionary["red_tick"]
        except commands.CommandError:
            can_run = self.context.bot.emoji_dictionary["red_tick"]
        embed.add_field(
            name="Required Permissions",
            value=(
                f"Can Use: {can_run}\n"
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


class HelpCommand(commands.Cog):
    def __init__(self, avi):
        self.HCne = avi.help_command
        self.avi = avi
        self.avi.help_command = HelpEmbeded(
            verify_checks=True,
            command_attrs=dict(
                hidden=True,
                aliases=["halp", "helps", "hlp", "hlep", "hep"],
                brief="Why do you need help with the help command? Oh well, Here it is anyways",
                usage="[command|module]",
            )
        )

    def cog_unload(self):
        self.avi.help_command = self.HCne


def setup(avi):
    avi.add_cog(HelpCommand(avi))
