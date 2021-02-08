import discord
import os
import json
import asyncio
import datetime
import time
import pymongo
from discord.ext import commands, tasks
import aiohttp
import psutil

class botinfo(commands.Cog, name="bot utilities"):
    def __init__(self, avimetry):
        self.avimetry = avimetry
#On Ready
    @commands.Cog.listener()
    async def on_ready(self):
        timenow=datetime.datetime.now().strftime("%I:%M %p")
        print('------\n'
              'Succesfully logged in. Bot Info Below:\n'
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
            return str(reaction.emoji) in ['<:yesTick:777096731438874634>', '<:noTick:777096756865269760>'] and user != self.avimetry.user and user==ctx.author
        try:
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
    @config.group(invoke_without_command=True, brief="Configure logging")
    @commands.has_permissions(administrator=True)
    async def logging(self, ctx):
        await ctx.send_help("config logging")   
    @logging.command(name="channel", brief="Configure logging channel")
    @commands.has_permissions(administrator=True)
    async def _channel(self, ctx, channel:discord.TextChannel):
        await self.avimetry.logs.upsert({"_id": ctx.guild.id, "logging_channel": channel.id})
        await ctx.send(f"Set logging channel to {channel}")
    @logging.command(brief="Configure delete logging")
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx, toggle:bool):
        await self.avimetry.logs.upsert({"_id": ctx.guild.id, "delete_log": toggle})
        await ctx.send(f"Set on_message_delete logs to {toggle}")
    @logging.command(brief="Configure edit logging")
    @commands.has_permissions(administrator=True)
    async def edit(self, ctx, toggle:bool):
        await self.avimetry.logs.upsert({"_id": ctx.guild.id, "edit_log": toggle})
        await ctx.send(f"Set on_message_edit logs to {toggle}")
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
    @counting.command(brief="Set the count in the counting channel")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def setcount(self, ctx, count:int):
        await self.avimetry.config.upsert({"_id": ctx.guild.id, "current_count":count})
        await ctx.send(f"Set the count to {count}")
    @counting.command(brief="Set the channel for counting")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def channel(self, ctx, channel:discord.TextChannel):
        await self.avimetry.config.upsert({"_id": ctx.guild.id, "counting_channel":channel.id})
        await ctx.send(f"Set the counting channel to {channel}")
    #Bot Info Command
    @commands.command()
    async def about(self, ctx):
        cool=await self.avimetry.config.find(message.guild.id)
        embed=discord.Embed(title="Info about Avimetry")
        embed.add_field(name="Developer", value="avi#4927")
        embed.add_field(name="Ping", value=f"`{round(self.avimetry.latency * 1000)}ms`")
        embed.add_field(name="Guild Count", value=f"{len(self.avimetry.guilds)} Guilds")
        embed.add_field(name="User Count", value=f"{len(self.avimetry.users)} Users")
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent(interval=None)}%")
        embed.add_field(name="RAM Usage", value=f"{psutil.virtual_memory().percent}%")
        embed.add_field(name="Bot Invite", value="[here](https://discord.com/oauth2/authorize?client_id=756257170521063444&scope=bot&permissions=2147483647)")
        embed.add_field(name="Commands", value=len(self.avimetry.commands))
        embed.add_field(name="Prefix for this server", value=cool["prefix"])
        embed.set_thumbnail(url=ctx.me.avatar_url)
        await ctx.send(embed=embed)
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
        message = await ctx.send_raw("Pinging...")
        end = time.perf_counter()
        duration = (end - start) * 1000
        pingembed=discord.Embed(title="🏓 Pong!")
        pingembed.add_field(name="Bot's Ping", value=f"`{round(self.avimetry.latency * 1000)}ms`")
        pingembed.add_field(name="Message Ping", value=f'`{round(duration)}ms`')
        await asyncio.sleep(.5)
        await message.edit(content="", embed=pingembed)
#Source Command
    #Removing or modifying this command is not allowed as stated in the license. If you do use this code, you have to make your bot's source public.
    @commands.command(brief="Sends the bot's source")
    async def source(self, ctx):
        source_embed=discord.Embed(title=f"{self.avimetry.user.name}'s source code", timestamp=datetime.datetime.utcnow())
        if self.avimetry.user.id!=756257170521063444:
            source_embed.description="This bot is made by [avi/jbkn](https://discord.com/users/750135653638865017). It is run off of this [source code](https://github.com/jbkn/avimetry).\nKeep the license in mind"
        else:
            source_embed.description="Here is my [source code](https://github.com/jbkn/avimetry) made by [avi](https://discord.com/users/750135653638865017).\nMake sure you follow the license."
        await ctx.send(embed=source_embed)
#Invite Command
    @commands.group(invoke_without_command=True)
    async def invite(self, ctx):
        invite_embed=discord.Embed(title=f"{self.avimetry.user.name} Invite", description="Invite me to your server! Here are the invite links.\n•Invite with [all permissions](https://discord.com/oauth2/authorize?client_id=756257170521063444&scope=bot&permissions=2147483647)\n•Invite with [administrator permissions](https://discord.com/oauth2/authorize?client_id=756257170521063444&scope=bot&permissions=8)\n•Invite with [no permissions](https://discord.com/oauth2/authorize?client_id=756257170521063444&scope=bot&permissions=8)")
        invite_embed.set_thumbnail(url=self.avimetry.user.avatar_url)
        await ctx.send(embed=invite_embed)
    @invite.command()
    async def bot(self, ctx, bot: discord.Member):
        bot_invite=discord.Embed()
        bot_invite.set_thumbnail(url=bot.avatar_url)
        if bot.bot:
            bot_invite.title=f"{bot.name} Invite"
            bot_invite.description=f"Invite {bot.name} to your server! Here are the invite links.\n•Invite with [all permissions](https://discord.com/oauth2/authorize?client_id={bot.id}&scope=bot&permissions=2147483647)\n•Invite with [administrator permissions](https://discord.com/oauth2/authorize?client_id={bot.id}&scope=bot&permissions=8)\n•Invite with [no permissions](https://discord.com/oauth2/authorize?client_id={bot.id}&scope=bot&permissions=8)"
        else:
            bot_invite.title=f"{bot.name} Invite"
            bot_invite.description=f"That is not a bot. Make sure you mention a bot."
        await ctx.send(embed=bot_invite)

def setup(avimetry):
    avimetry.add_cog(botinfo((avimetry)))