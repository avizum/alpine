import discord
import os
import datetime
from discord.ext import commands
import subprocess 
import asyncio
class cogs(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry
    def cog_unload(self):
        self.avimetry.load_extension("cogs.owner")
        print("asd")

#Load Command
    @commands.command(brief="Loads a module if it was disabled.")
    @commands.is_owner()
    async def load(self, ctx, extension=None):
        if extension==None:
            embed=discord.Embed(title="Load Modules", timestamp=datetime.datetime.utcnow())
            for filename in os.listdir('./avimetrybot/cogs'):
                if filename.endswith('.py'):
                    try:
                        self.avimetry.load_extension(f'cogs.{filename[:-3]}')
                    except Exception as e:
                        embed.add_field(name=f"<:noTick:777096756865269760> {filename}", value=f"Load was not successful: {e}", inline=True)
            await ctx.send(embed=embed)
            return
        try:
            self.avimetry.load_extension(f"cogs.{extension}")
            loadsuc=discord.Embed()
            loadsuc.add_field(name="<:yesTick:777096731438874634> Module Enabled", value=f"The **{extension}** module has been enabled.", inline=False)
            await ctx.send(embed=loadsuc)
        except Exception as load_error:
            noload=discord.Embed()
            noload.add_field(name="<:noTick:777096756865269760> Module was not loaded", value=load_error, inline=False)
            await ctx.send(embed=noload)

#Unload Command
    @commands.command(brief="Unloads a module if it is being abused.")
    @commands.is_owner()
    async def unload(self, ctx, extension=None):
        if extension==None:
            embed=discord.Embed(title="Unload Modules", timestamp=datetime.datetime.utcnow())
            for filename in os.listdir('./avimetrybot/cogs'):
                if filename.endswith('.py'):
                    try:
                        self.avimetry.unload_extension(f'cogs.{filename[:-3]}')
                    except Exception as e:
                        embed.add_field(name=f"<:noTick:777096756865269760> {filename}", value=f"Unload was not successful: {e}", inline=True)
            await ctx.send(embed=embed)
            return
        try:    
            self.avimetry.unload_extension(f'cogs.{extension}')
            unloadsuc=discord.Embed()
            unloadsuc.add_field(name="<:yesTick:777096731438874634> Module Disabled", value=f"The **{extension}** module has been disabled.", inline=False)
            await ctx.send (embed=unloadsuc)
        except Exception as unload_error:
            unloudno=discord.Embed()
            unloudno.add_field(name="<:noTick:777096756865269760> Module not unloaded", value=unload_error)
            await ctx.send(embed=unloudno)

#Reload Command
    @commands.command(brief="Reloads a module if it is not working.", usage="[extension]")
    @commands.is_owner()
    async def reload(self, ctx):
        embed=discord.Embed(title="Reload Modules", description="Reloaded all Modules sucessfully.", timestamp=datetime.datetime.utcnow())
        for filename in os.listdir('./avimetrybot/cogs'):
            if filename.endswith('.py'):
                try:
                    self.avimetry.reload_extension(f'cogs.{filename[:-3]}')
                except Exception as e:
                    embed.description="Reloaded all Modules sucessfully except the one(s) listed below:"
                    embed.add_field(name=f"<:noTick:777096756865269760> {filename}", value=f"Reload was not successful: {e}", inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def devmode(self, ctx, toggle:bool):
        await ctx.send(f"dev mode is now {toggle}")
        self.avimetry.devmode=toggle

    @commands.command(brief="Pulls from GitHub and then reloads all modules")
    @commands.is_owner()
    async def sync(self, ctx):
        sync_embed=discord.Embed(title="Syncing with GitHub", description="Please Wait...")
        edit_sync=await ctx.send_raw(embed=sync_embed)
        await asyncio.sleep(2)
        output=[]
        output.append(f'`{subprocess.getoutput("git pull")}`')
        sync_embed.description="\n".join(output)
        sync_embed.timestamp=datetime.datetime.utcnow()
        sync_embed.title="Synced With GitHub"
        await edit_sync.edit(embed=sync_embed)


def setup(avimetry):
    avimetry.add_cog(cogs(avimetry))