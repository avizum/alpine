import discord
import os
import json
import asyncio
import datetime
import time
from discord.ext import commands, tasks
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice

class botinfo(commands.Cog, name="Bot Information"):
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
        await asyncio.sleep(15)
        await self.avimetry.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='for commands'))
        await asyncio.sleep(15)
        await self.avimetry.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="'a.'"))
        await asyncio.sleep(15)
        await self.avimetry.change_presence(activity=discord.Game('discord.gg/zpj46np'))
        await asyncio.sleep(15)
        await self.avimetry.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name='ROBLOX'))
        await asyncio.sleep(15)
    @status_task.before_loop
    # pylint: disable=no-member
    async def before_status_task(self):
        await self.avimetry.wait_until_ready()
#On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        await self.avimetry.change_presence(status=discord.Status.idle)
        print(f'------\n'
              'Succesfully logged in as\n'
              f'Username: {self.avimetry.user.name}\n'
              f'Bot ID: {self.avimetry.user.id}\n'
              f'Login Time (UTC): {datetime.datetime.utcnow()}\n'
              '------'
        )

#Shutdown Command
    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.message.delete()
        sd=discord.Embed()
        sd.add_field(name="Shutting Down", value=f"You called the shutdown command, {self.avimetry.user.name} is now shutting down.")
        aa=await ctx.send(embed=sd)
        await asyncio.sleep(5)
        await aa.delete() 
        await self.avimetry.logout()

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