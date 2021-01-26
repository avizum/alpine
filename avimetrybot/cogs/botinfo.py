import discord
import os
import json
import asyncio
import datetime
import time
import pymongo
from discord.ext import commands, tasks
import aiohttp

class botinfo(commands.Cog, name="bot utilities"):
    def __init__(self, avimetry):
        # pylint: disable=no-member
        self.avimetry = avimetry
        self.status_task.start()
    def cog_unload(self):
        # pylint: disable=no-member
        self.status_task.cancel()
        
#Loop Presence
    @tasks.loop(seconds=1)
    async def status_task(self):
        await self.avimetry.change_presence(activity=discord.Game('Need Help? | a.help'))
        await asyncio.sleep(60)
        await self.avimetry.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='for commands'))
        await asyncio.sleep(60)
        await self.avimetry.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="'a.'"))
        await asyncio.sleep(60)
        await self.avimetry.change_presence(activity=discord.Game('discord.gg/zpj46np'))
        await asyncio.sleep(60)
        await self.avimetry.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name='ROBLOX'))
        await asyncio.sleep(60)
    @status_task.before_loop
    # pylint: disable=no-member
    async def before_status_task(self):
        await self.avimetry.wait_until_ready()

#On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        timenow=datetime.datetime.now().strftime("%I:%M %p")
        print('------\n'
              'Succesfully logged in as\n'
              f'Username: {self.avimetry.user.name}\n'
              f'Bot ID: {self.avimetry.user.id}\n'
              f'Login Time: {datetime.date.today()} at {timenow}\n'
              '------'
        )
#Mention prefix
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author==self.avimetry.user:
            return
        if message.content=="<@!756257170521063444>":
            cool=await self.avimetry.config.find(message.guild.id)
            await message.channel.send(f"Hey {message.author.mention}, the prefix for **{message.guild.name}** is `{cool['prefix']}`")
#Shutdown Command
    @commands.command(brief="Shutdown the bot")
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.message.delete()
        sm = discord.Embed()
        sm.add_field(name=f"{self.avimetry.user.name} shutdown", value="Are you sure you want to shut down?")
        rr=await ctx.send(embed=sm)
        reactions = ['<:yesTick:777096731438874634>', '<:noTick:777096756865269760>']
        for reaction in reactions:
            await rr.add_reaction(reaction)
        def check(reaction, user):
            return str(reaction.emoji) in ['<:yesTick:777096731438874634>', '<:noTick:777096756865269760>'] and user != self.avimetry.user
        try:
            # pylint: disable = unused-variable
            reaction, user = await self.avimetry.wait_for('reaction_add', check=check, timeout=60)
        except asyncio.TimeoutError:
            to=discord.Embed()
            to.add_field(name=f"{self.avimetry.user.name} shutdown", value="Timed Out.")
            await rr.edit(embed=to)
            await rr.clear_reactions()
        else:
            if str(reaction.emoji) == '<:yesTick:777096731438874634>':
                rre=discord.Embed()
                rre.add_field(name=f"{self.avimetry.user.name} shutdown", value="Shutting down...")
                await rr.edit(embed=rre)
                await rr.clear_reactions()
                await asyncio.sleep(5)
                await rr.delete()
                await self.avimetry.logout()
            if str(reaction.emoji) == '<:noTick:777096756865269760>':
                rre2=discord.Embed()
                rre2.add_field(name=f"{self.avimetry.user.name} shutdown", value="Shut down has been cancelled.")
                await rr.edit(embed=rre2)
                await rr.clear_reactions()
                await asyncio.sleep(5)
                await rr.delete()
#Config Command
    @commands.group(invoke_without_command=True, brief="The base config command, use this configure settings")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def config(self, ctx):
          await ctx.send_help("config")
#Config Prefix Commnad
    @config.command(brief="Change the prefix of this server")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def prefix(self, ctx, new_prefix):
        await self.avimetry.config.upsert({"_id": ctx.guild.id, "prefix": new_prefix})
        cp=discord.Embed()
        cp.add_field(name="<:yesTick:777096731438874634> Set Prefix", value=f"The prefix for **{ctx.guild.name}** is now `{new_prefix}`")
        await ctx.send(embed=cp)      
#Config Verification Gate Command
    @config.group(brief="Verification gate configuration for this server", aliases=["vgate", "verificationg", "vg"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def verificationgate(self, ctx):
        await ctx.send_help("config verificationgate")

    @verificationgate.command(brief="Toggle the verification gate")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def toggle(self, ctx, bool: bool):
        await self.avimetry.config.upsert({"_id":ctx.guild.id, "verification_gate":bool})
        await ctx.send(f"Verification Gate is now {bool}")

    @verificationgate.command(brief="Set the role to give when a member finishes verification.")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def role(self, ctx, role:discord.Role):
        await self.avimetry.config.upsert({"_id":ctx.guild.id, "gate_role":role.id})
        await ctx.send(f"The verification gate role is set to {role}")
#Config Counting Command
    @config.group(invoke_without_command=True, brief="Configure counting settings")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def counting(self, ctx):
        await ctx.send_help("config counting")
#Counting Set Count Command
    @counting.command(brief="Set the count in the counting channel")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def setcount(self, ctx, count:int):
        await self.avimetry.config.upsert({"_id": ctx.guild.id, "current_count":count})
        await ctx.send(f"Set the count to {count}")
#Counting Set Channel Command
    @counting.command(brief="Set the channel for counting")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def channel(self, ctx, channel:discord.TextChannel):
        await self.avimetry.config.upsert({"_id": ctx.guild.id, "counting_channel":channel.id})
        await ctx.send(f"Set the counting channel to {channel}")
#Bot Info Command
    @commands.command()
    async def info(self, ctx):
        info=discord.Embed()
        info.add_field(name=f"{self.avimetry.user.name} Information", value=f"Discord Py Version: {discord.__version__}\nPython Version: 3.9\nGuilds: {len(self.avimetry.guilds)}\nMembers: {len(self.avimetry.users)}\nBot Invite link: [here](https://discord.com/oauth2/authorize?client_id={self.avimetry.user.id}&scope=bot&permissions=2147483647)", inline=False)
        info.add_field(name="Bot Status", value=f"Ping: `{round(self.avimetry.latency * 1000)}ms`")
        await ctx.send(embed=info)
        
#Uptime Command
    @commands.command(brief="Get the bot's uptime")
    async def uptime(self, ctx):
        delta_uptime = datetime.datetime.utcnow() - self.avimetry.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        ue = discord.Embed(title="Current Uptime", description=f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds")
        await ctx.send(embed=ue)

#Ping Command
    @commands.command(brief="Gets the bot's ping.")
    async def ping(self, ctx):
        start = time.perf_counter()
        message = await ctx.send("Pinging...")
        end = time.perf_counter()
        duration = (end - start) * 1000
        pingembed=discord.Embed(title="🏓 Pong!")
        pingembed.add_field(name="Bot's Ping", value=f"`{round(self.avimetry.latency * 1000)}ms`")
        pingembed.add_field(name="Message Ping", value=f'`{round(duration)}ms`')
        await asyncio.sleep(.5)
        await message.edit(content="", embed=pingembed)
    
#Source Command
    @commands.command(brief="Sends the bot's source")
    async def source(self, ctx):
        source_embed=discord.Embed(title=f"{self.avimetry.user.name}'s source code", timestamp=datetime.datetime.utcnow())
        if self.avimetry.user.id!=756257170521063444:
            source_embed.description="The owner of this bot is not the creator of this bot. It is run off of this [source code](https://github.com/jbkn/avimetry 'Hello there from avi#0005')."
        else:
            source_embed.description="Here is my [source code](https://github.com/jbkn/avimetry)."
        await ctx.send(embed=source_embed)

def setup(avimetry):
    avimetry.add_cog(botinfo((avimetry)))