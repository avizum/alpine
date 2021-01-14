import discord
import os
import datetime
from discord.ext import commands

class Cogs(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry
      
#Load Command
    @commands.command(brief="Loads a module if it was disabled.")
    @commands.is_owner()
    async def load(self, ctx, extension):
        try:
            self.avimetry.load_extension(f"cogs.{extension}")
            loadsuc=discord.Embed()
            loadsuc.add_field(name="<:yesTick:777096731438874634> Module Enabled", value=f"The **{extension}** module has been enabled.", inline=False)
            await ctx.send(embed=loadsuc)
        except commands.ExtensionAlreadyLoaded:
            noload=discord.Embed()
            noload.add_field(name="<:noTick:777096756865269760> Module Already Loaded", value=f"The **{extension}** module is already enabled.", inline=False)
            await ctx.send(embed=noload)
        except commands.ExtensionNotFound:
            notfound=discord.Embed()
            notfound.add_field(name="<:noTick:777096756865269760> Module Not Found", value=f"The **{extension}** module does not exist.", inline=False)
            await ctx.send(embed=notfound)

#Unload Command
    @commands.command(brief="Unloads a module if it is being abused.")
    @commands.is_owner()
    async def unload(self, ctx, extension):
        try:    
            self.avimetry.unload_extension(f'cogs.{extension}')
            unloadsuc=discord.Embed()
            unloadsuc.add_field(name="<:yesTick:777096731438874634> Module Disabled", value=f"The **{extension}** module has been disabled.", inline=False)
            await ctx.send (embed=unloadsuc)
        except commands.ExtensionNotLoaded:
            nounload=discord.Embed()
            nounload.add_field(name="<:noTick:777096756865269760> Not Loaded",value=f"The **{extension}** module is not loaded. You can not unload an unloaded module.")
            await ctx.send(embed=nounload)

#Reload Command
    @commands.command(brief="Reloads a module if it is not working.")
    @commands.is_owner()
    async def reload(self, ctx, extension):
        try:
            self.avimetry.reload_extension(f'cogs.{extension}')
            reloadsuc=discord.Embed()
            reloadsuc.add_field(name="<:yesTick:777096731438874634> Module Reloaded", value=f"The **{extension}** module has been reloaded.", inline=False)
            await ctx.send (embed=reloadsuc)
        except commands.ExtensionNotLoaded:
            noreload=discord.Embed()
            noreload.add_field(name="<:noTick:777096756865269760> Not Loaded", value=f"The **{extension}** module is not loaded. You can not reload a module that is not loaded.")
            await ctx.send(embed=noreload)

    @commands.group(brief="Developer Load", invoke_with_subcommand=True)
    @commands.is_owner()
    async def dev(self, ctx):
        await ctx.send("haha you thought")

def setup(avimetry):
    avimetry.add_cog(Cogs(avimetry))