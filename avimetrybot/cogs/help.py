import discord
from discord.ext import commands, tasks
import datetime

class HCEmbed(commands.HelpCommand):
    def get_ending_note(self):
        return 'Use {0}{1} [command] or [module] for more info on a command or module.'.format(self.clean_prefix, self.invoked_with)

    def get_command_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Bot Commands')
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
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)
        
    async def send_cog_help(self, cog):
        embed = discord.Embed(title='{0.qualified_name} Commands'.format(cog))
        if cog.description:
            embed.description = cog.description
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or 'No Description', inline=True)
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name)
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.short_doc or 'No description', inline=True)
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed=discord.Embed(title="Command: {0.qualified_name}".format(command))
        embed.add_field(name=self.get_command_signature(command), value=command.short_doc or 'No description', inline=False)
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)
    
    async def command_not_found(self, command):
        embed=discord.Embed(title="Help command")
        embed.add_field(name=f"Command or Module does not exist", value='Command "{0}" is not a command. Make sure you capitalized and spelled it correctly.'.format(command))
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

class Help(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry
        self.avimetry.help_command = HCEmbed(
             command_attrs=dict(
                hidden=True,
                aliases=['h', 'halp', 'helps']
             )
        )

def setup(avimetry):
    avimetry.add_cog(Help(avimetry))
