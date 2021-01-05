import discord
import os
import datetime
from discord.ext import commands

class Cogs(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry
      
#Load Command
    @commands.command(brief="Loads a module if it was disabled.")
    @commands.has_permissions(administrator=True)
    async def load(self, ctx, extension):
        try:
            self.avimetry.load_extension(f"cogs.{extension}")
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

#Unload Command
    @commands.command(brief="Unloads a module if it is being abused.")
    @commands.has_permissions(administrator=True)
    async def unload(self, ctx, extension):
        try:    
            self.avimetry.unload_extension(f'cogs.{extension}')
            unloadsuc=discord.Embed()
            unloadsuc.add_field(name="<:aviSuccess:777096731438874634> Module Disabled", value=f"The **{extension}** module has been disabled.", inline=False)
            await ctx.send (embed=unloadsuc)
        except commands.ExtensionNotLoaded:
            nounload=discord.Embed()
            nounload.add_field(name="<:aviError:777096756865269760> Not Loaded",value=f"The **{extension}** module is not loaded. You can not unload an unloaded module.")
            await ctx.send(embed=nounload)

#Reload Command
    @commands.command(brief="Reloads a module if it is not working.")
    @commands.has_permissions(administrator=True)
    async def reload(self, ctx, extension):
        try:
            self.avimetry.reload_extension(f'cogs.{extension}')
            reloadsuc=discord.Embed()
            reloadsuc.add_field(name="<:aviSuccess:777096731438874634> Module Reloaded", value=f"The **{extension}** module has been reloaded.", inline=False)
            await ctx.send (embed=reloadsuc)
        except commands.ExtensionNotLoaded:
            noreload=discord.Embed()
            noreload.add_field(name="<:aviError:777096756865269760> Not Loaded", value=f"The **{extension}** module is not loaded. You can not reload a module that is not loaded.")
            await ctx.send(embed=noreload)

#Greload Command
    @commands.command(brief="Reload all modules")
    @commands.has_permissions(administrator=True)
    async def greload(self, ctx):
        ebbb = await ctx.send("Reloading Modules")
        ap = list()
        for filename in os.listdir('./avimetrybot/cogs'):
            if filename.endswith('.py'):
                self.avimetry.reload_extension(f'cogs.{filename[:-3]}')
                ap.append(filename[:-3])
                yes = ", "
        eb = discord.Embed(timestamp=datetime.datetime.utcnow())
        eb.add_field(name="<:aviSuccess:777096731438874634> Global Reload", value=f"__Reloaded Modules:__\n `{yes.join(ap)}`")
        await ebbb.edit(content="", embed=eb, delete_after=30)

def setup(avimetry):
    avimetry.add_cog(Cogs(avimetry))