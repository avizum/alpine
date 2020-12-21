import discord
import os
import json
import asyncio

from discord.ext import commands

class OnReady(commands.Cog):
    def __init__(self, avibot):
        self.avibot = avibot

    
    async def status_task(self):
        while True:
            await self.avibot.change_presence(activity=discord.Game('Need Help? | a.help'))
            await asyncio.sleep(60)
            await self.avibot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='for commands'))
            await asyncio.sleep(60)
            await self.avibot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="'a.'"))
            await asyncio.sleep(60)
            await self.avibot.change_presence(activity=discord.Game('discord.gg/zpj46np'))
            await asyncio.sleep(60)
            await self.avibot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name='Sleeping Battles'))
            await asyncio.sleep(60)

    @commands.Cog.listener()
    async def on_ready(self):
        game = discord.Game("avibot() is online!")
        await self.avibot.change_presence(status=discord.Status.idle, activity=game)
        await asyncio.sleep(5)
        print('Logged in as')
        print(self.avibot.user.name)
        print(self.avibot.user.id)
        print('------')
        self.avibot.loop.create_task(self.status_task())

    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.message.delete()
        sd=discord.Embed()
        sd.add_field(name="Shutting Down", value="You called the shutdown command, avimetry() is now shutting down.")
        await ctx.send(embed=sd)
        await self.avibot.change_presence(activity=discord.Game('Shutting down'))
        await asyncio.sleep(5)
        await self.avibot.logout()

def setup(avibot):
    avibot.add_cog(OnReady((avibot)))