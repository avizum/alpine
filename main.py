import discord
import os
import time
import asyncio
import json
import datetime
from discord.ext import commands, tasks
from itertools import cycle
from dotenv import load_dotenv

#ps aux | grep python

#Get Bot Token
load_dotenv()
avitoken = os.getenv('Bot_Token')
avitoken2 = os.getenv('Bot_Token2')

#Command Prefix and Intents

def prefix(client, message):
    if message.guild is None:
        return [str("a.")]
    else:
        with open("files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        return prefixes[str(message.guild.id)]

intents=discord.Intents.all()
avibot = commands.Bot(command_prefix = prefix, case_insensitive=True, intents=intents)

#No Commands in DMs
@avibot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

#Load Cogs
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        avibot.load_extension(f'cogs.{filename[:-3]}')


#Load Command
@avibot.command()
@commands.has_permissions(manage_roles=True)
async def load(ctx, extension):
    try:
        avibot.load_extension(f"cogs.{extension}")
        loadsuc=discord.Embed()
        loadsuc.add_field(name="<:aviSuccess:777096731438874634> Module Enabled", value=f"The **{extension}** module has been enabled.", inline=False)
        await ctx.send(embed=loadsuc)
    except commands.ExtensionAlreadyLoaded:
        noload=discord.Embed()
        noload.add_field(name="<:aviError:777096756865269760> Module Already Loaded", value=f"The **{extension}** module is already enabled.", inline=False)
        await ctx.send(embed=noload)
    except commands.ExtensionNotFound:
        notfound=discord.Embed()
        notfound.add_field(name="<:aviError:777096756865269760> Module Not Found", value=f"The **{extension}** module does not exist.", inline=False)
        await ctx.send(embed=notfound)
@load.error
async def loadErr(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        mra=discord.Embed(title="Command: Load")
        mra.add_field(name="Description:", value="Loads a module if it is not loaded.", inline=False)
        mra.add_field(name="Example:", value="`a.load [module]`")
        await ctx.send(embed=mra)
    if  isinstance(error, commands.MissingPermissions):
        noloadperm=discord.Embed()
        noloadperm.add_field(name="<:aviError:777096756865269760> No Permission", value="You do not have have the required permissions to use the `a.load` command.", inline=False)
        await ctx.send(embed=noloadperm)

#Unload Command
@avibot.command()
@commands.has_permissions(manage_roles=True)
async def unload(ctx, extension):
    try:    
        avibot.unload_extension(f'cogs.{extension}')
        unloadsuc=discord.Embed()
        unloadsuc.add_field(name="<:aviSuccess:777096731438874634> Module Disabled", value=f"The **{extension}** module has been disabled.", inline=False)
        await ctx.send (embed=unloadsuc)
    except commands.ExtensionNotLoaded:
        nounload=discord.Embed()
        nounload.add_field(name="<:aviError:777096756865269760> Not Loaded",value=f"The **{extension}** module is not loaded. You can not unload an unloaded module.")
        await ctx.send(embed=nounload)
@unload.error
async def unloadErr(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        mra=discord.Embed(title="Command: Unload")
        mra.add_field(name="Description:", value="Unloads a module if it is being abused or if something goes wrong.", inline=False)
        mra.add_field(name="Example:", value="`a.unload [module]`")
        await ctx.send(embed=mra)
    if  isinstance(error, commands.MissingPermissions):
        nounloadperm=discord.Embed()
        nounloadperm.add_field(name="<:aviError:777096756865269760> No Permission", value="You do not have have the required permissions to use the `a.unload` command.", inline=False)
        await ctx.send(embed=nounloadperm)

#Reload Command
@avibot.command(brief="Reload module", description="If a module is not working properly, use reload to get it to work again.")
@commands.has_permissions(manage_roles=True)
async def reload(ctx, extension):
    try:
        avibot.reload_extension(f'cogs.{extension}')
        reloadsuc=discord.Embed()
        reloadsuc.add_field(name="<:aviSuccess:777096731438874634> Module Reloaded", value=f"The **{extension}** module has been reloaded.", inline=False)
        await ctx.send (embed=reloadsuc)
    except commands.ExtensionNotLoaded:
        noreload=discord.Embed()
        noreload.add_field(name="<:aviError:777096756865269760> Not Loaded", value=f"The **{extension}** module is not loaded. You can not reload a module that is not loaded.")
        await ctx.send(embed=noreload)
    
@reload.error
async def reloadErr(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        mra=discord.Embed(title="Command: Reload")
        mra.add_field(name="Description:", value="Reloads a module if it is not working correctly.", inline=False)
        mra.add_field(name="Example:", value="`a.reload [module]`")
        await ctx.send(embed=mra)
    if  isinstance(error, commands.MissingPermissions):
        noreloadperm=discord.Embed()
        noreloadperm.add_field(name="<:aviError:777096756865269760> No Permission", value="You do not have have the required permissions to use the `a.reload` command.", inline=False)
        await ctx.send(embed=noreloadperm)

class HCEmbed(commands.HelpCommand):
    def get_ending_note(self):
        return 'Use {0}{1} [command] for more info on a command.\nUse {0}{1} [module] for more info on a module.'.format(self.clean_prefix, self.invoked_with)

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
        embed.add_field(name=f"Command does not exist",value="Command '{0}' is not a command. Make sure you spelled it correctly.".format(command))
        embed.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=embed)
avibot.help_command = HCEmbed()

#Log-In
avibot.run(avitoken, bot=True)
