import discord
from discord.ext import commands
import random
import time
import datetime
import json
import sys
import traceback

class ErrorHandler(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry

#Command Error
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        pre = await self.avimetry.get_prefix(ctx.message)

        error = getattr(error, 'original', error)
        
        if isinstance(error, commands.CommandNotFound):
            a = discord.Embed(color=discord.Color.red())
            a.add_field(name="<:noTick:777096756865269760> Invalid Command", value=f"{error}. \n ")
            a.set_footer(text=f"Use '{pre}help' if you need help.")
            await ctx.send(embed=a, delete_after=10)
        
        elif isinstance(error, commands.BotMissingPermissions):
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp])
            bnp=discord.Embed(color=discord.Color.red())
            bnp.add_field(name="<:noTick:777096756865269760> No Permission", value=f"I do not have permissions to do that. \nRequired Permission(s): `{missing_perms}`", inline=False)
            await ctx.send(embed=bnp, delete_after=10)
        
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            cd=discord.Embed(color=discord.Color.red())
            cd.add_field(name="<:noTick:777096756865269760> Command on cooldown", value=f"Please wait {error.retry_after:.2f} seconds before running `{pre}{ctx.command.name}` again")
            await ctx.send(embed=cd, delete_after=10) 
        
        elif isinstance(error, commands.MissingPermissions):
            await ctx.message.delete()
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp])
            missing_perms.replace("_", " ")
            np=discord.Embed(color=discord.Color.red())
            np.add_field(name="<:noTick:777096756865269760> No Permission", value=f"You do not have permissions to use the`{pre}{ctx.command.name}`command. \nRequired Permission(s): `{missing_perms}`", inline=False)
            await ctx.send(embed=np, delete_after=10)

        elif isinstance(error, commands.MissingRequiredArgument):
            pre = await self.avimetry.get_prefix(ctx.message)
            ctx.command.reset_cooldown(ctx)
            a = discord.Embed(color=discord.Color.red())
            a.add_field(name="<:noTick:777096756865269760> Missing required argument(s)", value=f'Here are the missing argument(s): "{error.param.name}"')
            a.set_footer(text=f"Use '{pre}help' if you need help.")
            await ctx.send(embed=a, delete_after=10)

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("This command is disabled. The command will be enabled when the command is done.")

        elif isinstance(error, commands.NotOwner):
            no=discord.Embed(color=discord.Color.red())
            no.add_field(name="<:noTick:777096756865269760> No Permission", value=f"You are not a bot owner, so you can't use `{pre}{ctx.command.name}`.", inline=False)
            await ctx.send(embed=no, delete_after=10)

        elif isinstance(error, commands.BadArgument):
            ba = discord.Embed(color=discord.Color.red())
            ba.add_field(name="<:noTick:777096756865269760> Bad Argument", value=error)
            await ctx.send(embed=ba, delete_after=10)
        
        elif isinstance(error, commands.BotMissingPermissions):
            bm = discord.Embed(color=discord.Color.red())
            bm.add_field(name="<:noTick:777096756865269760> I have no permission", value=f"I do not have permission to do that, Please give me these permission(s) `{missing_perms}`")
            await ctx.send(embed=bm, delete_after=10)

        elif isinstance(error, commands.TooManyArguments):
            await ctx.send(f"{error}")

        elif isinstance(error, discord.Forbidden):
            forbidden=discord.Embed(color=discord.Color.red())
            forbidden.add_field(name="<:noTick:777096756865269760> No Permission", value="I do not have permission to do that. Make sure I have permission")
            await ctx.send(embed=forbidden, delete_after=10)
            await ctx.send(error)
        
        elif isinstance(error, commands.NoPrivateMessage):
            NoPrivate=discord.Embed()
            NoPrivate.add_field(name="<:noTick:777096756865269760> No commands in Direct Messages", value="Commands do not work in DMs. They only work in guilds/servers.")
            await ctx.send(embed=NoPrivate)
        else:
            sexc = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            ee = discord.Embed(color=discord.Color.red())
            ee.add_field(name="<:noTick:777096756865269760> Unknown Error", value="Uh oh, avi messaged up again! The error has been recorded and avi will cry. No worries, he will fix it.")
            try:
                await ctx.send(embed=ee, delete_after=10)
                chanel = self.avimetry.get_channel(797362270593613854)
                ff = discord.Embed(title=f"{self.avimetry.user.name} Error", description=f"```{sexc}```")
                await chanel.send(embed=ff)
            except:
                return
            
def setup(avimetry):
    avimetry.add_cog(ErrorHandler(avimetry))