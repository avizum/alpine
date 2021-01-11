import discord
import os
import json
import asyncio
import datetime
import time
from discord.ext import commands, tasks

class botinfo(commands.Cog, name="Bot Utilities"):
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
        print(f'------\n'
              'Succesfully logged in as\n'
              f'Username: {self.avimetry.user.name}\n'
              f'Bot ID: {self.avimetry.user.id}\n'
              f'Login Time (UTC): {datetime.datetime.utcnow()}\n'
              '------'
        )

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
            
    @commands.command(brief="Set the prefix of the server.")
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, nprefix):
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)

        prefixes[str(ctx.guild.id)] = nprefix

        with open("./avimetrybot/files/prefixes.json", "w") as f:
            json.dump(prefixes, f, indent=4)
        
        cp=discord.Embed()
        cp.add_field(
            name="<:yesTick:777096731438874634> Set Prefix",
            value=f"The prefix for **{ctx.guild.name}** is now `{nprefix}`"
        )
        await ctx.send(embed=cp)             
        
#Bot Info Command
    @commands.command()
    async def info(self, ctx):
        a = discord.Embed(title=f"{self.avimetry.user.name}")
        a.add_field(name="WIP", value="Command not working yet")
        
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
        pingembed.add_field(name="Message Ping", value='`{:.2f}ms`'.format(duration))
        await asyncio.sleep(.5)
        await message.edit(content="", embed=pingembed)
    
def setup(avimetry):
    avimetry.add_cog(botinfo((avimetry)))