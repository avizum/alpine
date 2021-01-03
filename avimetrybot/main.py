import discord
import os
import asyncio
import json
import datetime
import logging
from discord.ext import commands, tasks
from itertools import cycle
from dotenv import load_dotenv

#ps aux | grep python
#Get Bot Token
load_dotenv()
avitoken = os.getenv('Bot_Token')
avitoken2 = os.getenv('Bot_Token2')
avitoken3 = os.getenv('Bot_Token3')

#Command Prefix and Intents
def prefix(client, message):
    if message.guild is None:
        return [str("a.")]
    else:
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        return prefixes[str(message.guild.id)]
intents=discord.Intents.all()
avimetry = commands.Bot(command_prefix = prefix, case_insensitive=True, intents=intents)
avimetry.launch_time = datetime.datetime.utcnow()

#No Commands in DMs
@avimetry.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

@tasks.loop(seconds=60)
async def loop():
    try:
        avimetry.load_extension("./avimetrybot/cogs/loads")
    except commands.ExtensionAlreadyLoaded:
        return
loop.start()

#Load Cogs
avimetry.load_extension('jishaku')
for filename in os.listdir('./avimetrybot/cogs'):
    if filename.endswith('.py'):
        avimetry.load_extension(f'cogs.{filename[:-3]}')

#Uptime
@avimetry.command()
async def uptime(ctx):
    delta_uptime = datetime.datetime.utcnow() - avimetry.launch_time
    hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    ue = discord.Embed(title="Current Uptime", description=f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds")
    await ctx.send(embed=ue)

#HCEmbed
class HCEmbed(commands.HelpCommand):
    def get_ending_note(self):
        return '• Use {0}{1} [command] for more info on a command.\n• Use {0}{1} [module] for more info on a module.\n '.format(self.clean_prefix, self.invoked_with)

    def get_command_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Bot Commands', timestamp=datetime.datetime.utcnow())
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
                embed.add_field(name=name, value=value)
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title='{0.qualified_name} Commands'.format(cog))
        if cog.description:
            embed.description = cog.description
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '---', inline=False)
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name)
        if group.help:
            embed.description = group.help

        if isinstance(group, commands.Group):
            filtered = await self.filter_commands(group.commands, sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '---', inline=False)
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed=discord.Embed(title="Command: {0.qualified_name}".format(command), timestamp=datetime.datetime.utcnow())
        embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '---', inline=False)
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)
    
    async def command_not_found(self, command):
        embed=discord.Embed(title="Help command", timestamp=datetime.datetime.utcnow())
        embed.add_field(name=f"Command does not exist",value="Command '{0}' is not a command. Make sure you capitalized and spelled it correctly.".format(command))
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)
avimetry.help_command = HCEmbed()

#Log-In
avimetry.run(avitoken, bot=True)
