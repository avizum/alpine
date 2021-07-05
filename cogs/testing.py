import discord
from discord.ext import commands

class Test(commands.Cog):
    
    @commands.command()
    async def jalksdja(self, ctx):
        await ctx.send('a')

def setup(bot):
    bot.add_cog(Test(bot))