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
import random
import humanize
import pytz
import typing

class Miscellaneous(commands.Cog):
    
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
        if len(options)>10:
            raise commands.BadArgument("You can only have ten options in a poll")
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

#Pick Command
    @commands.command(brief="Pick one of your options")
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def pick(self, ctx, *options: str):
        if len(options)<2:
            raise commands.BadArgument("You need to have at least two options.")
        if len(options)>10:
            raise commands.BadArgument("You can only have ten options.")
        await ctx.send(f"I picked: '{random.choice(options)}'")

#Info Command
    @commands.command(brief="Gets a member's information")
    # pylint: disable=unsubscriptable-object
    async def uinfo(self, ctx, *, member : typing.Union[discord.Member, discord.User]=None):
    # pylint: enable=unsubscriptable-object
        if member==None:
            member=ctx.author
        if isinstance(member, discord.User):
            ie = discord.Embed(title="User Information", description="This user in not in this server",timestamp=datetime.datetime.utcnow(), color=member.color)
            ie.add_field(name="User Name", value=str(member))
            ie.add_field(name="User ID", value=member.id)
            ie.add_field(name="Creation Date", value=f"{humanize.naturaldate(member.created_at)} ({humanize.naturaltime(member.created_at)})", inline=False)
            ie.set_thumbnail(url=member.avatar_url)
        else:
            userroles = list()
            jnr = ", "
            for roles in member.roles:
                userroles.append(roles.mention)
                if ctx.guild.default_role.mention in userroles:
                    userroles.remove(ctx.guild.default_role.mention)
            ie = discord.Embed(title="User Information", timestamp=datetime.datetime.utcnow(), color=member.color)
            ie.add_field(name="User Name", value=str(member))
            ie.add_field(name="User ID", value=member.id)
            ie.add_field(name="Nickname", value=member.nick)
            ie.add_field(name="Join Date", value=f"{humanize.naturaldate(member.joined_at)} ({humanize.naturaltime(member.joined_at)})", inline=False)
            ie.add_field(name="Creation Date", value=f"{humanize.naturaldate(member.created_at)} ({humanize.naturaltime(member.created_at)})", inline=False)
            if member.raw_status=="online":
                member_status="Online <:status_online:810683593193029642>"
            elif member.raw_status=="offline":
                member_status="Offline <:status_offline:810683581541515335>"
            elif member.raw_status=="idle":
                member_status="Idle <:status_idle:810683571269664798>"
            elif member.raw_status=="dnd":
                member_status="Do not Disturb <:status_dnd:810683560863989805>"
            elif member.raw_status=="streaming":
                member_status="Streaming <:status_streaming:810683604812169276>"
            ie.add_field(name="Status", value=member_status)
            ie.add_field(name="Top Role", value=member.top_role.mention, inline=False)
            ie.add_field(name=f"Roles [{len(userroles)}]", value=f"{jnr.join(userroles)}", inline=False)
            ie.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=ie)

#QR code command
    @commands.command(brief="Make a qr code ")
    async def qr(self, ctx, *, content):
        qr_embed=discord.Embed()
        qr_embed.add_field(name="QR code", value="Here is your qr code")
        qr_embed.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?data={content}&size=250x250")
        await ctx.send(embed=qr_embed)

#Time command
    @commands.group(brief="Gets the time for a member", invoke_without_command=True)
    async def time(self, ctx, *, member:discord.Member=None):
        if member==None:
            member=ctx.author
        data=await self.avimetry.time_zones.find(member.id)
        try:
            timezone=data[str('time_zone')]
        except KeyError:
            return await ctx.send("That user does not have a time zone set.")
        timezone=pytz.timezone(timezone)
        time=datetime.datetime.now(timezone)
        format_time=time.strftime("%A, %B %d at %I:%M %p")
        time_embed=discord.Embed(description=format_time)
        time_embed.set_author(name=f"Time for {member.display_name}", icon_url=member.avatar_url)
        if member.display_name.endswith("s"):
            member_name=f"{member.display_name}'"
        else:
            member_name=f"{member.display_name}'s"
        time_embed.set_footer(text=f"{member_name} timezone: {timezone}")
        await ctx.send(embed=time_embed)
    
    @time.command(brief="Sets your timezone")
    async def set(self, ctx, *, timezone):
        try:
            timezones=pytz.timezone(timezone)
        except KeyError:
            raise commands.BadArgument("That is not a valid time zone. [Here](https://gist.github.com/Soheab/3bec6dd6c1e90962ef46b8545823820d) are the valid time zones.")
        await self.avimetry.time_zones.upsert({"_id":ctx.author.id, "time_zone": str(timezones)})
        await ctx.send(f"Set timezone to {timezones}")

    @commands.command(brief="Get the jump link for the channel that you mention")
    async def firstmessage(self, ctx, *, channel:discord.TextChannel=None):
        if channel==None:
            channel=ctx.channel
        messages=await channel.history(limit=1, oldest_first=True).flatten()
        if len(messages[0].content)>100:
            mg_cnt=messages[0].content[:100]
            pass
        mg_cnt=messages[0].content
        embed_message=discord.Embed(title=f"First Message of #{channel.name}", description=f"Here is the message link. [jump]({messages[0].jump_url})\n\n>>> {mg_cnt}")
        await ctx.send(embed=embed_message)

    @commands.command()
    async def test(self, ctx):
        await ctx("'fdkfj'")

def setup(avimetry):
    avimetry.add_cog(Miscellaneous(avimetry))