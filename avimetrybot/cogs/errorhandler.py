import discord
from discord.ext import commands
import random
import time
import datetime
import json

class ErrorHandler(commands.Cog):
    
    def __init__(self, avimetry):
        self.avimetry = avimetry

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        global pre
        pre = prefixes[str(ctx.guild.id)]
        
        if isinstance(error, commands.CommandNotFound):
            a = discord.Embed()
            a.add_field(name="<:aviError:777096756865269760> Invalid Command", value=f"{error}")
            a.set_footer(text=f"Use `{pre}help` if you need help.")
            await ctx.send(embed=a, delete_after=10)

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            cd=discord.Embed()
            cd.add_field(name="<:aviError:777096756865269760> Command on cooldown", value=f"Please wait {error.retry_after:.2f} seconds before running `{pre}{ctx.command.name}` again")
            await ctx.send(embed=cd, delete_after=10) 
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.message.delete()
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp])
            np=discord.Embed()
            np.add_field(name="<:aviError:777096756865269760> No Permission", value=f"You do not have permissions to use the`{pre}{ctx.command.name}`command. \nRequired Permissions: `{missing_perms}`", inline=False)
            await ctx.send(embed=np, delete_after=10)

        if isinstance(error, commands.MissingRequiredArgument):
            prefix= await self.avimetry.get_prefix(ctx.message)
            ctx.command.reset_cooldown(ctx)
            cu = discord.Embed(title=f"Command: {ctx.command.name}")
            cu.add_field(name=f"Usage:", value=f"**{prefix}{ctx.command.name} {ctx.command.signature}**\n{ctx.command.brief}" or "No description.", inline=False)
            cu.set_footer(text=f"If you need help, use '{prefix}help'. \nThe help command has all the information.")
            await ctx.send(embed=cu, delete_after=15)

        if isinstance(error, commands.DisabledCommand):
            await ctx.send("This command is disabled. The command will be enabled when the command is done.")

        if isinstance(error, commands.NotOwner):
            no=discord.Embed()
            no.add_field(name="<:aviError:777096756865269760> No Permission", value=f"You are not an owner, so you can't use `{pre}{ctx.command.name}`.", inline=False)
            await ctx.send(embed=no, delete_after=10)


def setup(avimetry):
    avimetry.add_cog(ErrorHandler(avimetry))