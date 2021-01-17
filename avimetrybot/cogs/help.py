import discord
from discord.ext import commands, tasks
import datetime

class HCEmbed(commands.HelpCommand):
    def gending_note(self):
        return 'Use {0}{1} [command] or [module] for more info on a command or module.'.format(self.clean_prefix, self.invoked_with)

    def gcommand_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    async def send_error_message(self, command):
        return

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Help Menu', description=f"Command Syntax\n>>> ```[optional] <--- Optional Argument\n<requred> <--- Requred Argument```")
        description = self.context.bot.description
        if description:
            embed.description = description

        for cog, commands in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name
            filtered = await self.filter_commands(commands, sort=True)
            if filtered:
                value = '\u002c '.join(c.name for c in commands)
                if cog and cog.description:
                    value = '{0}\n{1}'.format(cog.description, value)
                embed.add_field(name=name, value=f"`{value}`", inline=True)
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)
        
    async def send_cog_help(self, cog):
        embed = discord.Embed(title='{0.qualified_name} Commands'.format(cog))
        if cog.description:
            embed.description = cog.description
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            usage=command.short_doc
            if not usage:
                usage="No Description"
            embed.add_field(name=self.gcommand_signature(command), value=f"`{usage}`", inline=True)
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name)
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                usage=command.short_doc
                if not usage:
                    usage="No Description"
                embed.add_field(name=self.gcommand_signature(command), value=f"`{usage}`", inline=False)
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed=discord.Embed(title="Command: {0.qualified_name}".format(command))
        usage=command.short_doc
        if not usage:
            usage="No Description"
        embed.add_field(name=self.gcommand_signature(command), value=f"`{usage}`", inline=False)
        embed.set_footer(text=self.gending_note())
        await self.get_destination().send(embed=embed)
    
    async def command_not_found(self, command):
        embed=discord.Embed(title="Help Menu")
        embed.add_field(name=f"Command/Module does not exist", value='"{0}" is not a command/module.\nMake sure you capitalized and spelled it correctly.'.format(command))
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
                aliases=['h', 'halp', 'helps','cmds', 'commands', 'cmd']
             )
        )

    def cog_unload(self):
        self.avimetry.help_command = self.HCne
def setup(avimetry):
    avimetry.add_cog(Help(avimetry))
