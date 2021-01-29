import discord
import os
import datetime
from discord.ext import commands

class cogs(commands.Cog):
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
            await ctx.send(embed=loadsuc, delete_after=10)
        except Exception as load_error:
            noload=discord.Embed()
            noload.add_field(name="<:noTick:777096756865269760> Module was not loaded", value=load_error, inline=False)
            await ctx.send(embed=noload, delete_after=10)

#Unload Command
    @commands.command(brief="Unloads a module if it is being abused.")
    @commands.is_owner()
    async def unload(self, ctx, extension):
        try:    
            self.avimetry.unload_extension(f'cogs.{extension}')
            unloadsuc=discord.Embed()
            unloadsuc.add_field(name="<:yesTick:777096731438874634> Module Disabled", value=f"The **{extension}** module has been disabled.", inline=False)
            await ctx.send (embed=unloadsuc, delete_after=10)
        except Exception as unload_error:
            unloudno=discord.Embed()
            unloudno.add_field(name="<:noTick:777096756865269760> Module not unloaded", value=unload_error)
            await ctx.send(embed=unloudno, delete_after=10)

#Reload Command
    @commands.command(brief="Reloads a module if it is not working.")
    @commands.is_owner()
    async def reload(self, ctx, extension):
        try:
            self.avimetry.reload_extension(f'cogs.{extension}')
            reloadsuc=discord.Embed()
            reloadsuc.add_field(name="<:yesTick:777096731438874634> Module Reloaded", value=f"The **{extension}** module has been reloaded.", inline=False)
            await ctx.send (embed=reloadsuc)
        except Exception as reload_error:
            noreload=discord.Embed()
            noreload.add_field(name="<:noTick:777096756865269760> Not Loaded", value=reload_error)
            await ctx.send(embed=noreload, delete_after=10)

    @commands.command(brief="Reload all modules")
    @commands.is_owner()
    async def greload(self, ctx):
        embed=discord.Embed(title="Reloaded Modules", timestamp=datetime.datetime.utcnow())
        for filename in os.listdir('./avimetrybot/cogs'):
            if filename.endswith('.py'):
                try:
                    self.avimetry.reload_extension(f'cogs.{filename[:-3]}')
                    embed.add_field(name=f"<:yesTick:777096731438874634> {filename}", value="Reload was successful", inline=True)
                except Exception as e:
                    embed.add_field(name=f"<:noTick:777096756865269760> {filename}", value=f"Reload was not successful: {e}", inline=True)
        await ctx.send(embed=embed, delete_after=10)

    @commands.command()
    @commands.is_owner()
    async def devmode(self, ctx, toggle:bool):
        await ctx.send(f"dev mode is now {toggle}")
        self.avimetry.devmode=toggle

def setup(avimetry):
    avimetry.add_cog(cogs(avimetry))