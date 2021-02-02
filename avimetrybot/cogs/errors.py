import discord
from discord.ext import commands
import datetime
import traceback, sys, os

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
    
        if isinstance(error, commands.CommandNotFound):
            return
        
        elif isinstance(error, commands.BotMissingPermissions):
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp])
            bnp=discord.Embed(title="Give me permissions", description=f"Hey, I do not have the required permisisons to do that. Here are the permissions that I need:\n`{missing_perms}`",color=discord.Color.red())
            await ctx.send(embed=bnp, delete_after=10)
        
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            cd=discord.Embed(title="Slow down", description=f"Hey, **{ctx.command.name}** has a cooldown. Please wait `{round(error.retry_after)}` seconds before using it again.", color=discord.Color.red())
            await ctx.send(embed=cd, delete_after=10) 
        
        elif isinstance(error, commands.MissingPermissions):
            await ctx.message.delete()
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp])
            missing_perms.replace("_", " ")
            np=discord.Embed(title="Missing permissions", description=f"You do not have permissions to use {ctx.command.name}. Here are the permissions that you need:\n`{missing_perms}`", color=discord.Color.red())
            await ctx.send(embed=np, delete_after=10)

        elif isinstance(error, commands.MissingRequiredArgument):
            pre = await self.avimetry.get_prefix(ctx.message)
            ctx.command.reset_cooldown(ctx)
            a = discord.Embed(title="Invalid command syntax", description=f"You invoked this command incorrectly, Here is the correct syntax\n{ctx.command.signature}.",color=discord.Color.red())
            a.set_footer(text=f"Use '{pre}help' if you need help.")
            await ctx.send(embed=a, delete_after=10)

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("This command is disabled. The command will be enabled when the command is done.")

        elif isinstance(error, commands.NotOwner):
            no=discord.Embed(title="Missing Permissions", description="Only owners can run this command.",color=discord.Color.red())
            await ctx.send(embed=no, delete_after=10)

        elif isinstance(error, commands.BadArgument):
            ba = discord.Embed(color=discord.Color.red())
            ba.add_field(name="<:noTick:777096756865269760> Bad argument", value=error)
            await ctx.send(embed=ba, delete_after=10)
        
        elif isinstance(error, commands.BotMissingPermissions):
            mp = error.missing_perms
            missing_perms = " ".join([str(elem) for elem in mp])
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
            NoPrivate=discord.Embed(color=discord.Color.red())
            NoPrivate.add_field(name="<:noTick:777096756865269760> No commands in Direct Messages", value="Commands do not work in DMs. They only work in guilds/servers.")
            await ctx.send(embed=NoPrivate)
        
        elif isinstance(error, commands.MaxConcurrencyReached):
            max_uses=discord.Embed(color=discord.Color.red())
            max_uses.add_field(name="<:noTick:777096756865269760> Limited Command", value=f"Sorry, `{ctx.command.name}` has limited usage. Please try again later.")
            await ctx.send(embed=max_uses)
        else:
            long_exception = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            ee = discord.Embed(color=discord.Color.red())
            short_exception=''.join(traceback.format_exception_only(type(error), error))
            ee.add_field(name="<:noTick:777096756865269760> Unknown Error", value=f"Uh oh, an error has occured! Do not worry, the error has been recorded.\n\n`{short_exception}`")
            try:
                await ctx.send(embed=ee, delete_after=10)
                chanel = self.avimetry.get_channel(797362270593613854)
                ff = discord.Embed(title=f"{self.avimetry.user.name} Error", description=f"```{long_exception}```")
                await chanel.send(embed=ff)
            except:
                return
            
def setup(avimetry):
    avimetry.add_cog(errorhandler(avimetry))