import discord
from discord import Webhook, AsyncWebhookAdapter
import time
from discord.ext import commands
import json
import datetime
import aiohttp
import unicodedata
import sr_api
import asyncio

class miscellaneous(commands.Cog):
    
    def __init__(self, avimetry):
        self.avimetry = avimetry
#CoViD-19 Stats
    @commands.command()
    async def covid(self, ctx, *, country):
        pre = await self.avimetry.get_prefix(ctx.message)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://coronavirus-19-api.herokuapp.com/countries/{country}') as resp:
                    js_in=await resp.json()
                    countries = js_in["country"]
                    totalCases = js_in["cases"]
                    todayCases = js_in["todayCases"]
                    casesPerMil = js_in["casesPerOneMillion"]
                    activeCases = js_in["active"]
                    criticalCases = js_in["critical"]
                    totalDeaths = js_in["deaths"]
                    todayDeaths = js_in["todayDeaths"]
                    deathsPerMil = js_in["deathsPerOneMillion"]
                    recovered = js_in["recovered"]
                    tests = js_in["totalTests"]
                    testPerMil = js_in["testsPerOneMillion"]

                    e = discord.Embed(title=f"COVID-19 Status for {countries}", description="Cases are not updated live, so it may not be very accurate at times.")
                    e.add_field(name="Total Cases:", value=totalCases, inline=True)
                    e.add_field(name="Cases Today:", value=todayCases, inline=True)
                    e.add_field(name="Cases Per 1M:", value=casesPerMil, inline=True)
                    e.add_field(name="Active Cases:", value=activeCases, inline=True)
                    e.add_field(name="Critical Cases:", value=criticalCases, inline=True)
                    e.add_field(name="Total Deaths:", value=totalDeaths, inline=True)
                    e.add_field(name="Deaths Today:", value=todayDeaths, inline=True)
                    e.add_field(name="Deaths Per 1M:", value=deathsPerMil, inline=True)
                    e.add_field(name="Recovered:", value=recovered, inline=True)
                    e.add_field(name="Tests Taken:", value=tests, inline=True)
                    e.add_field(name="Tests Taken Per 1M:", value=testPerMil, inline=True)
                    await ctx.send(embed=e)        
        except:
            a = discord.Embed()
            a.add_field(name="<:noTick:777096756865269760> Invalid Country", value=f"{country} is not a country, or the API may be down. Please try again later")
            a.set_footer(text=f"Use '{pre}help' if you need help.")
            await ctx.send(embed=a, delete_after=10)

#Poll command
    @commands.command(brief="Launch a poll for users to vote to.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def poll(self, ctx, question, *options: str):
        if len(options)<2:
            raise commands.BadArgument("You need to have at least two options in the poll.")
            
        await ctx.message.delete()
        if len(options) == 2 and options[0] == 'Yes' and options[1] == 'No':
            reactions = ['<:yesTick:777096731438874634>', '<:noTick:777096756865269760>']
        elif len(options) == 2 and options[0] == 'yes' and options[1] == 'no':
            reactions = ['<:yesTick:777096731438874634>', '<:noTick:777096756865269760>']
        else:
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        description = []
        for x, option in enumerate(options):
            description +='\n\n{} {}'.format(reactions[x], option)
        embed = discord.Embed(title=question, description="".join(description))
        embed.set_footer(text=f"Poll from: {str(ctx.author)}")
        react_message = await ctx.send(embed=embed)
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(text=f"Poll from: {str(ctx.author)}\nPoll ID: {react_message.id}")
        await react_message.edit(embed=embed)
        
#Info Command
    @commands.command(brief="Gets a member's information")
    async def uinfo(self, ctx, *, member : discord.Member):
        userroles = list()
        jnr = ", "

        userroles.append("@everyone")
        for roles in member.roles:
            userroles.append(roles.mention)
            if ctx.guild.default_role.mention in userroles:
                userroles.remove(ctx.guild.default_role.mention)
        

        ie = discord.Embed(title="User Information", description=f'User Information for {member.mention}:\n'
                                                          f'**Full Name:** {member.name}#{member.discriminator}\n'
                                                          f'**User ID:** {member.id}\n'
                                                          f'**Nickname:** {member.nick}\n' 
                                                          f'**Server Join Date:** {member.joined_at.strftime("%m/%d/%Y at %I:%M %p (UTC)")}\n'
                                                          f'**User Creation Date:** {member.created_at.strftime("%m/%d/%Y at %I:%M %p (UTC)")}\n' 
                                                          f'**Roles** [{len(userroles)}] {jnr.join(userroles)}', timestamp=datetime.datetime.utcnow())
        ie.set_thumbnail(url=member.avatar_url)
        ie.add_field(name="Server Permissions", value="wip")
        await ctx.send(embed=ie)

    @commands.command(brief="Make a qr code ")
    async def qr(self, ctx, *, content):
        qr_embed=discord.Embed()
        qr_embed.add_field(name="QR code", value="Here is your qr code")
        qr_embed.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?data={content}&size=250x250")
        await ctx.send(embed=qr_embed)

    @commands.command()
    async def charinfo(self, ctx, *, characters: str):
        def to_string(c):
            digit = f'{ord(c):x}'
            name = unicodedata.name(c, 'Name not found.')
            return f'`\\U{digit:>08}`: {name} - {c}\n[More Info](<http://www.fileformat.info/info/unicode/char/{digit}>)'
        msg = '\n'.join(map(to_string, characters))
        if len(msg) > 2000:
            return await ctx.send('Message too long. Sorry!')
        embed=discord.Embed(title=f"Character Information - {characters}", description=msg, timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)

        
def setup(avimetry):
    avimetry.add_cog(miscellaneous(avimetry))