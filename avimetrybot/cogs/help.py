import discord
from discord.ext import commands, tasks
import datetime
import os
import pathlib
from difflib import get_close_matches

class HCEmbed(commands.HelpCommand):

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

    def gending_note(self):
        return 'Use {0}{1} [command] or [module] for more info on a command or module.'.format(self.clean_prefix, self.invoked_with)
    
    def bnote(self):
        return ">>> `<> = required argument\n[] = optional argument`"

    def gcommand_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    async def send_error_message(self, command):
        return

    def get_destination(self):
        return self.context


    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Help Menu', description=f"{self.context.bot.user.name} {self.get_files()}\n\nThe prefix for **{self.get_destination().guild.name}** is `{self.clean_prefix}`")
        for cog, commands in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name.title()
            filtered = await self.filter_commands(commands, sort=True)
            if filtered:
                value=f"`{self.clean_prefix}{self.invoked_with} {name.lower()}`"
                embed.add_field(name=name, value=value, inline=False)
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)
   
    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f'{cog.qualified_name.title()} Commands', description=self.bnote())
        if cog.description:
            embed.description = cog.description
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            usage=command.short_doc
            if not usage:
                usage="No description provided, now go try doing it yourself"
            embed.add_field(name=f"{self.clean_prefix}{self.gcommand_signature(command)}", value=f"`{usage}`", inline=False)
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=f"Command Group: {group.qualified_name}", description=self.bnote())
        if group.short_doc:
            usage=group.short_doc
            if not usage:
                usage="No description provided, now go try doing it yourself"
            embed.add_field(name=f"{self.clean_prefix}{self.gcommand_signature(group)}", value=f"`{usage}`")

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                usage=command.short_doc
                if not usage:
                    usage="No description provided, now go try doing it yourself"
                embed.add_field(name=f"{self.clean_prefix}{self.gcommand_signature(command)}", value=f"`{usage}`", inline=False)
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed=discord.Embed(title="Command: {0.qualified_name}".format(command), description=self.bnote())
        usage=command.short_doc
        if not usage:
            usage="No description provided, now go try doing it yourself"
        embed.add_field(name=f"{self.clean_prefix}{self.gcommand_signature(command)}", value=f"`{usage}`", inline=False)
        alias = command.aliases
        if alias:
            embed.add_field(name="Aliases", value=f'`{", ".join(alias)}`', inline=False)

        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)
    
    async def command_not_found(self, string):
        embed=discord.Embed(title="Command Not Found")
        lol='\n'.join(get_close_matches(string, [i.name for i in self.context.bot.commands]))
        if lol:
            embed.description=f'"{string}" is not a command/module. Did you mean...\n`{lol}`'
        if not lol:
            embed.description=f'"{string}" is not a command/module and I couln\'t find any similar commands.'
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)
    
    async def subcommand_not_found(self, command, string):
        embed=discord.Embed(title="Help Menu")
        embed.add_field(name=f"Subcommand does not exist", value='"{0}" is not a subcommand of "{1}".'.format(string, command))
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

class Help(commands.Cog):
    def __init__(self, avimetry):
        self.HCne = avimetry.help_command
        self.avimetry = avimetry
        self.avimetry.help_command = HCEmbed(
             command_attrs=dict(
                hidden=True,
                aliases=['h', 'halp', 'helps','cmds', 'commands', 'cmd'],
                brief="Why do you need help with the help command? Oh well, Here it is anyways",
                usage="[command] or [module]"
             )
        )

    def cog_unload(self):
        self.avimetry.help_command = self.HCne
    
def setup(avimetry):
    avimetry.add_cog(Help(avimetry))
