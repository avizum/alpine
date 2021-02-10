import discord
from discord.ext import commands
import datetime
import traceback, sys, os
from difflib import get_close_matches
import re
import prettify_exceptions

class errorhandler(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry

#Command Error
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.author.id in self.avimetry.owner_ids:
            if self.avimetry.devmode==True:
                try:
                    await ctx.reinvoke()
                    return
                except:
                    return
            else:
                pass
        
        pre = await self.avimetry.get_prefix(ctx.message)
        error = getattr(error, 'original', error)
        try:
            command_name=ctx.command.name
        except Exception:
            pass
        '''
        if not ctx.invoked_with==None:
            command_name=ctx.command.name
        else:
            command_name=f"{ctx.command.parent.name} {ctx.command.name}"
        '''
        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.BotMissingPermissions):
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp])
            bnp=discord.Embed(title="Give me permissions", description=f"Hey, I do not have the required permisisons to do that. Here are the permissions that I need:\n`{missing_perms}`",color=discord.Color.red())
            await ctx.send(embed=bnp)
        
        elif isinstance(error, commands.CommandOnCooldown):
            cd=discord.Embed(title="Slow down", description=f"Hey, **{command_name}** has a cooldown. Please wait `{round(error.retry_after)}` seconds before using it again.", color=discord.Color.red())
            await ctx.send(embed=cd) 
        
        elif isinstance(error, commands.MissingPermissions):
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp])
            missing_perms.replace("_", " ")
            np=discord.Embed(title="Missing permissions", description=f"You do not have permissions to use {command_name}. Here are the permissions that you need:\n`{missing_perms}`", color=discord.Color.red())
            await ctx.send(embed=np)

        elif isinstance(error, commands.MissingRequiredArgument):
            pre = await self.avimetry.get_prefix(ctx.message)
            try:
                ctx.command.reset_cooldown(ctx)
            except Exception:
                pass
            a = discord.Embed(title="Invalid command syntax", description=f"You invoked this command incorrectly, Here is the correct syntax\n`{pre}{command_name} {ctx.command.signature}`.",color=discord.Color.red())
            a.set_footer(text=f"Use '{pre}help' if you need help.")
            await ctx.send(embed=a)

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("This command is not open yet.")

        elif isinstance(error, commands.NotOwner):
            no=discord.Embed(title="Missing Permissions", description="Only owners can run this command.",color=discord.Color.red())
            await ctx.send(embed=no)

        elif isinstance(error, commands.BadArgument):
            ba = discord.Embed(color=discord.Color.red())
            ba.add_field(name="<:noTick:777096756865269760> Bad argument", value=error)
            await ctx.send(embed=ba)
        
        elif isinstance(error, commands.TooManyArguments):
            await ctx.send(f"{error}")
            
        elif isinstance(error, commands.NoPrivateMessage):
            NoPrivate=discord.Embed(color=discord.Color.red())
            NoPrivate.add_field(name="<:noTick:777096756865269760> No commands in Direct Messages", value="Commands do not work in DMs. They only work in guilds/servers.")
            await ctx.send(embed=NoPrivate)
        
        elif isinstance(error, commands.MaxConcurrencyReached):
            max_uses=discord.Embed(color=discord.Color.red())
            max_uses.add_field(name="<:noTick:777096756865269760> Max Concurrency Reached", value=f"Sorry, `{command_name}` is at it's max concurrency. Please try again later.")
            await ctx.send(embed=max_uses)
        else:
            ctx.command.reset_cooldown(ctx)
            prettify_exceptions.DefaultFormatter().theme['_ansi_enabled'] = False
            long_exception = ''.join(prettify_exceptions.DefaultFormatter().format_exception(type(error), error, error.__traceback__))
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            ee = discord.Embed(color=discord.Color.red())
            short_exception=''.join(traceback.format_exception_only(type(error), error))
            myst_exception=await self.avimetry.myst.post(long_exception, syntax="python")
            ee.title="Avimetry Error" 
            ee.description=f"Uh oh, an error has occured! Do not worry, the error has been recorded.\n\n`Command {ctx.command.name} raised an exception: {short_exception}`\n For more info, see the [full exception]({str(myst_exception)})"
            try:
                await ctx.send(embed=ee)
                chanel = self.avimetry.get_channel(797362270593613854)
                ff = discord.Embed(title=f"{self.avimetry.user.name} Error", description=f"```{str(myst_exception)}```")
                await chanel.send(embed=ff)
            except:
                return
            
def setup(avimetry):
    avimetry.add_cog(errorhandler(avimetry))