import discord
import os
import json
import asyncio
import datetime
import time
from discord.ext import commands
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice

class OnReady(commands.Cog, name="Bot Information"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

#Loop Presence
    async def status_task(self):
        while True:
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
#On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        game = discord.Game(f"{self.avimetry.user.name} is online!")
        await self.avimetry.change_presence(status=discord.Status.idle, activity=game)
        print(f'------\n'
              'Succesfully logged in as\n'
              f'Username: {self.avimetry.user.name}\n'
              f'Bot ID: {self.avimetry.user.id}\n'
              f'Login Time (UTC): {datetime.datetime.utcnow()}\n'
              '------'
        )
        await asyncio.sleep(2)
        self.avimetry.loop.create_task(self.status_task())

#Shutdown Command
    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.message.delete()
        sd=discord.Embed()
        sd.add_field(name="Shutting Down", value=f"You called the shutdown command, {self.avimetry.user.name} is now shutting down.")
        await ctx.send(embed=sd)
        await self.avimetry.change_presence(activity=discord.Game('Shutting down'))
        await asyncio.sleep(5)
        await self.avimetry.logout()

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
        await message.edit(content="", embed=pingembed)
    
def setup(avimetry):
    avimetry.add_cog(OnReady((avimetry)))