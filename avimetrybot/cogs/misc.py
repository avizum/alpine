import discord
import time
from discord.ext import commands
import asyncio
import random
import json
import datetime
import subprocess
import os
import requests

class Miscellaneous(commands.Cog):
    
    def __init__(self, avimetry):
        self.avimetry = avimetry

#CoViD-19 Stats
    @commands.command()
    async def covid(self, ctx, country):
        pre = await self.avimetry.get_prefix(ctx.message)
        try:
            c = requests.get(f'https://coronavirus-19-api.herokuapp.com/countries/{country}')
            js_in = c.json()
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
            a.add_field(name="<:aviError:777096756865269760> Invalid Country", value=f"{country} is not a country, or the API may be down. Please try again later")
            a.set_footer(text=f"Use '{pre}help' if you need help.")
            await ctx.send(embed=a, delete_after=10)
#Study Hall Command
    @commands.group()
    async def studyhall(self, ctx):
        if ctx.invoked_subcommand is None:
            subcn=discord.Embed(title="Command: Studyhall")
            subcn.add_field(name="Description:", value="Gives you access to the studyhall VC and channel", inline=False)
            subcn.add_field(name="Example:", value="`a.studyhall [on | off]`", inline=False)
            await ctx.send(embed=subcn)
    @studyhall.command(brief="Puts yourself in to study hall.")
    async def on(self, ctx):
        member = ctx.author
        role = discord.utils.get(member.guild.roles, name="Studying")
        role2 = discord.utils.get(member.guild.roles, name="Member")
        sho=discord.Embed()
        sho.add_field(name="Study Hall", value=f"{member.mention} is now in study hall.", inline=False)
        await ctx.send(embed=sho)
        time.sleep(0.5)
        await discord.Member.add_roles(member, role)
        await discord.Member.remove_roles(member, role2)
    @studyhall.command(brief="Removes yourself from study hall.")
    async def off(self, ctx):
        member = ctx.author
        role = discord.utils.get(member.guild.roles, name="Studying")
        role2 = discord.utils.get(member.guild.roles, name="Member")
        shof = discord.Embed()
        shof.add_field(name="Study hall", value="Now exiting study hall...")
        await ctx.send(embed=shof)
        time.sleep(0.5)
        await discord.Member.remove_roles(member, role)
        await discord.Member.add_roles(member, role2)

#Poll command
    @commands.command(brief="Launch a poll for users to vote to.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def poll(self, ctx, question,  *options: str):
        if len(options) < 3:
            raise commands.MissingRequiredArgument(options)
        await ctx.message.delete()
        channel = self.avimetry.get_channel(774075297142013972)
        if len(options) == 2 and options[0] == 'Yes' and options[1] == 'No':
            reactions = ['<:aviSuccess:777096731438874634>', '<:aviError:777096756865269760>']
        elif len(options) == 2 and options[0] == 'yes' and options[1] == 'no':
            reactions = ['<:aviSuccess:777096731438874634>', '<:aviError:777096756865269760>']
        else:
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        description = []
        for x, option in enumerate(options):
            description +='\n\n {} {}'.format(reactions[x], option)
        embed = discord.Embed(title=question, description=''.join(description))
        embed.set_footer(text=f"Poll from: {ctx.author.name}#{ctx.author.discriminator}")
        react_message = await channel.send(embed=embed)
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(text=f"Poll from: {ctx.author.name}#{ctx.author.discriminator}\nPoll ID: {react_message.id}")
        await react_message.edit(embed=embed)
    
#Request Nick command
    @commands.command(brief="Requests a new nick name.")
    async def requestnick(self, ctx, *, rqnick):
        channels = self.avimetry.get_channel(787942179310010368)
        rq=discord.Embed()
        rq.add_field(name="Request Nickname", value=f"Your request has been sent. \nRequested Nickname: `{rqnick}`")
        ap=discord.Embed()
        ap.add_field(name="Incoming Request", value=f"{ctx.author.mention} requested to change their nickname to `{rqnick}` \nIf you want to change their nickname, use the command below to change their nickname \n`a.cnick {ctx.author.id} {rqnick}`")
        await ctx.send(embed=rq, delete_after=5)
        await channels.send(embed=ap)
        await ctx.message.add_reaction("<a:animyes:777100238573404171>")

#Info Command
    @commands.command(brief="Gets a member's information")
    async def uinfo(self, ctx, *, member : discord.Member):
        userroles = list()
        jnr = ", "
        for roles in member.roles:
            userroles.append(roles.name)
        ie = discord.Embed(title="User Informaion", description=f'User Information for {member.mention}:\n'
                                                          f'**Full Name:** {member.name}#{member.discriminator}\n'
                                                          f'**User ID:** {member.id}\n'
                                                          f'**Nickname:** {member.nick}\n' 
                                                          f'**Server Join Date:** {member.joined_at}\n'
                                                          f'**User Creation Date:** {member.created_at}\n' 
                                                          f'**Roles** [{len(userroles)}] {jnr.join(userroles)}', timestamp=datetime.datetime.utcnow())
        ie.set_thumbnail(url=member.avatar_url)
        ie.add_field(name="Server Permissions", value="wip")
        await ctx.send(embed=ie)
    
    @commands.command()
    async def example(self, ctx):
        e = discord.Embed(title="Title", description="Description i think 2048 char limit", timestamp=datetime.datetime.utcnow(), color=discord.Color.blurple())
        e.set_author(name="cool author", url="https://www.youtube.com")
        e.add_field(name="yes1", value="nice value1", inline=True)
        e.add_field(name="yes2", value="nice value2", inline=True)
        e.add_field(name="yes3", value="nice value3", inline=True)
        e.add_field(name="yes4", value="non inline value", inline=False)
        e.add_field(name="yes5", value="another non inline value", inline=False)
        e.set_thumbnail(url=ctx.author.avatar_url)
        e.set_footer(text="yes footer")
        await ctx.send(embed=e)

    
def setup(avimetry):
    avimetry.add_cog(Miscellaneous(avimetry))


