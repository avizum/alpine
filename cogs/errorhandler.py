import discord
from discord.ext import commands
import random
import time
import json

class ErrorHandler(commands.Cog):
    
    def __init__(self, avibot):
        self.avibot = avibot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        with open("files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        global pre
        pre = prefixes[str(ctx.guild.id)]
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            cd=discord.Embed()
            cd.add_field(name="<:aviError:777096756865269760> Command on cooldown", value=f"Please wait {error.retry_after:.2f} seconds before running `{pre}{ctx.command.name}` again")
            await ctx.send(embed=cd, delete_after=10) 
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.message.delete()
            np=discord.Embed()
            np.add_field(name="<:aviError:777096756865269760> No Permission", value=f"You do not have have the required permissions to use the `{pre}{ctx.command.name}` command.", inline=False)
            await ctx.send(embed=np, delete_after=10)

        if isinstance(error, commands.MissingRequiredArgument):
            ctx.command.reset_cooldown(ctx)
            await ctx.send(ctx.command.name)

        if isinstance(error, commands.CommandNotFound):
            print("Unknown command called, returning\n------")



def setup(avibot):
    avibot.add_cog(ErrorHandler(avibot))