import discord
from discord.ext import commands
import datetime
import traceback, sys, os
from difflib import get_close_matches
import re
import prettify_exceptions
import humanize

class ErrorHandler(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry

#Command Error
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if ctx.author.id in self.avimetry.owner_ids:
            if self.avimetry.devmode==True:
                try:
                    return await ctx.reinvoke()
                except:
                    return print(f"Could not reinvoke {ctx.command.name}")
            else:
                pass
        
        pre = await self.avimetry.get_prefix(ctx.message)
        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound):
            not_found_embed=discord.Embed(title="Invalid Command", color=discord.Color.red())
            not_found=ctx.invoked_with
            lol='\n'.join(get_close_matches(not_found, [i.name for i in ctx.bot.commands]))
            if not lol:
                return
            not_found_embed.description=f'I wasn\'t able to find a command called "{not_found}" . Did you mean...\n`{lol}`'
            not_found_embed.set_footer(text=f"Not what you meant? Use {pre}help to see the whole list of commands.")
            await ctx.send(embed=not_found_embed)
        
        elif isinstance(error, commands.CommandOnCooldown):
            cd=discord.Embed(title="Slow down", description=f"You are on cooldown. Try again in {humanize.naturaldelta(error.retry_after)}.", color=discord.Color.red())
            await ctx.send(embed=cd) 

        elif isinstance(error, commands.BotMissingPermissions):
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp]).replace("_", " ").replace("guild", "server")
            bnp=discord.Embed(title="Missing Permissions", description=f"I need the following permisisons to run this command:\n`{missing_perms}`",color=discord.Color.red())
            await ctx.send(embed=bnp)
        
        elif isinstance(error, commands.MissingPermissions):
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp]).replace("_", " ").replace("guild", "server")
            np=discord.Embed(title="Missing Permissions", description=f"You need the following permissions to run this command:\n`{missing_perms}`", color=discord.Color.red())
            await ctx.send(embed=np)
        
        elif isinstance(error, commands.NotOwner):
            no=discord.Embed(title="Missing Permissions", description="You need the following permissions to run this command:\n`bot owner`",color=discord.Color.red())
            await ctx.send(embed=no)

        elif isinstance(error, commands.MissingRequiredArgument):
            try:
                ctx.command.reset_cooldown(ctx)
            except Exception:
                pass
            a = discord.Embed(title="Missing Arguments", description=f"You forgot to put the `{error.param.name}` argument for this command.", color=discord.Color.red())
            await ctx.send(embed=a)

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("This command is not open yet.")

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
            max_uses.add_field(name="<:noTick:777096756865269760> Max Concurrency Reached", value=f"Sorry, is at it's max concurrency. Please try again later.")
            await ctx.send(embed=max_uses)
        else:
            ctx.command.reset_cooldown(ctx)
            prettify_exceptions.DefaultFormatter().theme['_ansi_enabled'] = False
            long_exception = ''.join(prettify_exceptions.DefaultFormatter().format_exception(type(error), error, error.__traceback__))
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            ee = discord.Embed(color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
            short_exception=''.join(traceback.format_exception_only(type(error), error))
            myst_exception=await self.avimetry.myst.post(long_exception, syntax="python")
            ee.title="Unknown Error" 
            ee.description=f"Oh no, avi messed up again. The error was logged and will be fixed in the next ten years.\n\n`{short_exception}`"
            try:
                await ctx.send(embed=ee)
                chanel = self.avimetry.get_channel(797362270593613854)
                ff = discord.Embed(title=f"{self.avimetry.user.name} Error", description=f"`{short_exception}`\n{str(myst_exception)}")
                await chanel.send(embed=ff)
            except:
                return
            
def setup(avimetry):
    avimetry.add_cog(ErrorHandler(avimetry))