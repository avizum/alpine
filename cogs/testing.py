import discord
from discord.ext import commands

class Test(commands.Cog):
    
    @commands.command()
    async def jalksdja(self, ctx):
        await ctx.send('a')

def setup(avi):
    avi.add_cog(Test(avi))