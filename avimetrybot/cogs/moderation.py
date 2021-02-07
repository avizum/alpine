import discord
from discord.ext import commands, tasks
from copy import deepcopy
from dateutil.relativedelta import relativedelta
import random
import time
import asyncio
import re
import datetime

time_regex = re.compile(r"(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}

class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        args=argument.lower()
        matches=re.findall(time_regex, args)
        time=0
        for key, value in matches:
            try:
                time+=time_dict[value]*float(key)
            except KeyError:
                raise(commands.BadArgument(f"{key} is not a number!"))
        return round(time)
        
class moderation(commands.Cog):
    
    def __init__(self, avimetry):
        self.avimetry = avimetry
        self.check_mutes.start()
        def cog_unload(self):
            self.check_mutes.cancel()
#Unmute Loop
    @tasks.loop(minutes=1)
    async def check_mutes(self):
        currentTime = datetime.datetime.now()
        mutes = deepcopy(self.avimetry.muted_users)
        for key, value in mutes.items():
            if value['muteDuration'] is None:
                continue

            unmuteTime = value['mutedAt'] + relativedelta(seconds=value['muteDuration'])

            if currentTime >= unmuteTime:
                guild = self.avimetry.get_guild(value['guildId'])
                member = guild.get_member(value['_id'])

                role = discord.utils.get(guild.roles, name="Muted")
                if role in member.roles:
                    await member.remove_roles(role)
                    try:
                        unmuted=discord.Embed()
                        unmuted.add_field(name="<:yesTick:777096731438874634> Unmuted", value=f"You have been unmuted in {member.guild.name}")
                        await member.send(embed=unmuted)
                    except discord.Forbidden:
                        return
                else:
                    try:
                        await self.avimetry.mutes.delete(member.id)
                        await self.avimetry.muted_users.pop(member.id)
                    except discord.Forbidden:
                        return
                await self.avimetry.mutes.delete(member.id)
                try:
                    self.avimetry.muted_users.pop(member.id)
                except KeyError:
                    pass
    
    @check_mutes.before_loop
    async def before_check_mutes(self):
        await self.avimetry.wait_until_ready()

#Clean Command    
    @commands.command(brief="Cleans bot messages", usage="[amount]")
    @commands.has_permissions(manage_messages=True)
    async def clean(self, ctx, limit=100):
        await ctx.message.delete()
        def avimetrybot(m):
            c1=m.author==self.avimetry.user
            return c1
        try:
            d1 = await ctx.channel.purge(limit=limit, check=avimetrybot, bulk=True)
        except discord.Forbidden:
            d1 = await ctx.channel.purge(limit=limit, check=avimetrybot, bulk=False)
        cm = await ctx.send("Cleaning...")
        ce=discord.Embed()
        ce.add_field(name="<:yesTick:777096731438874634> Clean Messages", value=f"Successfully deleted **{len(d1)}** messages")
        await cm.edit(content="", embed=ce, delete_after=10)

#Purge Command
    @commands.group(invoke_without_command=True, brief="Delete a number of messages in the current channel.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(5, 30, commands.BucketType.member)
    async def purge(self, ctx, amount: int):
        await ctx.message.delete()
        if amount == 0:
            pass
        elif amount > 250:
            a100=discord.Embed()
            a100.add_field(name="<:noTick:777096756865269760> No Permission", value="You can't purge more than 150 messages at a time.")
            await ctx.send(embed=a100, delete_after=10)
        else:
            authors = {}
            async for message in ctx.channel.history(limit=amount):
                if message.author not in authors:
                    authors[message.author] = 1
                else:
                    authors[message.author] += 1
            await asyncio.sleep(.1)
            purge_amount=await ctx.channel.purge(limit=amount)   
            msg = "\n".join([f"{author}: {amount}" for author, amount in authors.items()])

            pe=discord.Embed()
            pe.add_field(name="<:yesTick:777096731438874634> Purge Messages", value=f"Here are the results of the purged messages:\n`{msg}`\n\n Total Messages Deleted:`{len(purge_amount)}`")
            pe.set_footer(text="React with the emoji to delete this message")
            purge_results=await ctx.send(embed=pe)
            await purge_results.add_reaction("<:noTick:777096756865269760>")

            def check(reaction, user):
                return str(reaction.emoji) in "<:noTick:777096756865269760>" and user != self.avimetry.user and user==ctx.author
            try:
                reaction, user = await self.avimetry.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                pe.set_footer(text="Menu has timed out")
                await purge_results.edit(embed=pe)
            else:
                if str(reaction.emoji) == '<:noTick:777096756865269760>':
                    await purge_results.delete()

    @purge.command()	
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def match(self, ctx, amount: int, *, text):	
        await ctx.message.delete()
        def pmatch(m):	
            return text in m.content	
        await ctx.channel.purge(limit = amount, check = pmatch)	
        purgematch=discord.Embed()	
        purgematch.add_field(name="<:yesTick:777096731438874634> Purge Match", value=f"Purged {amount} messages containing {text}.")
    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def startswith(self, ctx, text:str, amount:int):
        await ctx.message.delete()
        def check(m):
            return m.content.startswith(text)
        purge_amount=await ctx.channel.purge(limit=amount, check=check)
        await ctx.send(f"Deleted {len(purge_amount)} messages that start with '{text}'")

#Lock Channel Command
    @commands.command(brief="Locks the mentioned channel.", usage="<channel> [reason]",timestamp=datetime.datetime.utcnow())
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx, channel : discord.TextChannel, *, reason="No Reason Provided"):
        await channel.set_permissions(ctx.guild.default_role, send_messages=False, read_messages=False)
        lc=discord.Embed()
        lc.add_field(name=":lock: Channel has been locked.", value=f"{ctx.author.mention} has locked down <#{channel.id}> with the reason of {reason}. Only Staff members can speak now.")
        await channel.send(embed=lc)

#Unlock Channel command
    @commands.command(brief="Unlocks the mentioned channel.", usage="<channel> [reason]",timestamp=datetime.datetime.utcnow())
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel : discord.TextChannel, *, reason="No Reason Provided"):
        await channel.set_permissions(ctx.guild.default_role, send_messages=None, read_messages=False)
        uc=discord.Embed()
        uc.add_field(name=":unlock: Channel has been unlocked.", value=f"{ctx.author.mention} has unlocked <#{channel.id}> with the reason of {reason}. Everyone can speak now.")
        await channel.send(embed=uc)
    
#Kick Command
    @commands.command(brief="Kicks a member from the server.", usage="<member> [reason]")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member : discord.Member, *, reason = "No reason was provided"):
        if member==ctx.message.author:
            e1=discord.Embed()
            e1.add_field(name="<:noTick:777096756865269760> No Permission", value="You can't kick yourself. That's just stupid.")
            await ctx.send(embed=e1, delete_after=10)
        elif member==self.avimetry.user:
            e2=discord.Embed()
            e2.add_field(name="<:noTick:777096756865269760> No Permission", value="You can't kick me, because that won't work.")
            await ctx.send(embed=e2, delete_after=10)
        elif member.top_role > ctx.author.top_role:
            e3=discord.Embed()
            e3.add_field(name="<:noTick:777096756865269760> No Permission", value="You can not kick someone that has a higher role than you. They must have a role under you.", inline=False)
            await ctx.send(embed=e3, delete_after=10)
        elif member.top_role== ctx.author.top_role:
            e4=discord.Embed()
            e4.add_field(name="<:noTick:777096756865269760> No Permission", value="You can not kick someone that has the same role as you. They must have a role under you.", inline=False)
            await ctx.send(embed=e4, delete_after=10)
        else:
            try:
                bae=discord.Embed(title=f"You have been kicked from {ctx.guild.name}", timestamp=datetime.datetime.utcnow())
                bae.add_field(name= "Moderator:", value=f"{ctx.author.name} \n`{ctx.author.id}`")
                bae.add_field(name="Reason:", value=f"{reason}")
                await member.send(embed=bae)
                await member.kick(reason=reason)
                kickembed=discord.Embed()
                kickembed.add_field(name="<:yesTick:777096731438874634> Kick Member", value=f"**{member}** has been kicked from the server.", inline=False)
                await ctx.send(embed=kickembed)
            except discord.HTTPException:
                await member.kick(reason=reason)
                kickembed=discord.Embed()
                kickembed.add_field(name="<:yesTick:777096731438874634> Kick Member", value=f"**{member}** has been kicked from the server, but I could not DM them.", inline=False)
                await ctx.send(embed=kickembed)

#Ban Command
    @commands.command(brief="Bans a member from the server", usage="<member> [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member : discord.Member, *, reason = "No reason was provided"):
        if member==ctx.message.author:
                mecma=discord.Embed()
                mecma.add_field(name="<:noTick:777096756865269760> No Permission", value="You can't ban yourself. That's just stupid.")
                await ctx.send(embed=mecma)
        elif member==self.avimetry.user:
                msau=discord.Embed()
                msau.add_field(name="<:noTick:777096756865269760> No Permission", value="You can't ban me, because that won't work.")
                await ctx.send(embed=msau)
        elif member.top_role > ctx.author.top_role:
                mtrgratr=discord.Embed()
                mtrgratr.add_field(name="<:noTick:777096756865269760> No Permission", value="You can not ban someone that has a higher role than you. They must have a role under you.", inline=False)
                await ctx.send(embed=mtrgratr)
        elif member.top_role== ctx.author.top_role:
            mtretatr=discord.Embed()
            mtretatr.add_field(name="<:noTick:777096756865269760> No Permission", value="You can not ban someone that has the same role as you. They must have a role under you.", inline=False)
            await ctx.send(embed=mtretatr)
        else:
            try:
                bae=discord.Embed(title=f"You have been banned from {ctx.guild.name}", timestamp=datetime.datetime.utcnow())
                bae.add_field(name= "Moderator:", value=f"{ctx.author.mention} \n`{ctx.author.id}`")
                bae.add_field(name="Reason:", value=f"{reason}")
                await member.send(embed=bae)
                await member.ban(reason=reason)
                banembed=discord.Embed()
                banembed.add_field(name="<:yesTick:777096731438874634> Ban Member", value=f"{member.mention} (`{member.id}`) has been banned from **{ctx.guild.name}**.", inline=False)
                await ctx.send(embed=banembed)
            except discord.HTTPException:
                await member.ban(reason=reason)
                banembed=discord.Embed()
                banembed.add_field(name="<:yesTick:777096731438874634> Ban Member", value=f"{member.mention} (`{member.id}`) has been banned from **{ctx.guild.name}**, but I could not DM them.", inline=False)
                await ctx.send(embed=banembed)

#Unban Command
    @commands.command(brief="Unbans a member from the server.", usage="<member_id> [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, member_id, *, reason="No reason was provided"):
        some_member=commands.MemberConverter().convert(ctx, member_id)
        await ctx.guild.unban(some_member)
        unbanenmbed=discord.Embed()
        unbanenmbed.add_field(name="<:yesTick:777096731438874634> Unban Member", value="Unbanned <@{member_id}> ({member_id}) from **{ctx.guild.name}**.", inline=False)
        await ctx.send(embed=unbanenmbed)

#Slowmode Command
    @commands.command(brief="Sets the slowmode in the current channel.")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        smembed=discord.Embed()
        smembed.add_field(name="<:yesTick:777096731438874634> Set Slowmode", value=f"Slowmode delay is now set to {seconds} seconds.")
        await ctx.send(embed=smembed)
   
#Mute command
    @commands.command(brief="Mutes a member.")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx, member : discord.Member, time: TimeConverter=None):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            no_muted_role=discord.Embed()
            no_muted_role.add_field(name="<:noTick:777096756865269760> Mute Failed", value=f"Couldn't mute {member.mention} because there is no role named Muted.")
            await ctx.send(embed=no_muted_role)
            return
        try:
            if self.avimetry.muted_users[member.id]:
                already_muted=discord.Embed()
                already_muted.add_field(name="<:noTick:777096756865269760> Mute Failed", value=f"{member.mention} is already muted")
                await ctx.send(embed=already_muted)
            return
        except KeyError:
            pass
        data={
            "_id": member.id,
            "mutedAt": datetime.datetime.now(),
            "muteDuration": time or None,
            "mutedBy": ctx.author.id,
            'guildId': ctx.guild.id
        }
        await self.avimetry.mutes.upsert(data)
        self.avimetry.muted_users[member.id]=data
        await member.add_roles(role)
        if not time: 
            unlimited_mute=discord.Embed()
            unlimited_mute.add_field(name="<:yesTick:777096731438874634> Muted Member", value=f"{member.mention} was muted with no unmute time.")
            await ctx.send(embed=unlimited_mute)
        else:
            minutes, seconds = divmod(time, 60)
            hours, minutes=divmod(minutes, 60)
            days, hours=divmod(hours, 24)
            if int(days):
                mute_days=discord.Embed()
                mute_days.add_field(name="<:yesTick:777096731438874634> Muted Member", value=f"{member.mention} was muted for {days} days, and {hours} hours.")
                await ctx.send(embed=mute_days)
            elif int(hours):
                mute_hours=discord.Embed()
                mute_hours.add_field(name="<:yesTick:777096731438874634> Muted Member", value=f"{member.mention} was muted for {hours} hours, and {minutes} minutes.")
                await ctx.send(embed=mute_hours)
            elif int(minutes):
                mute_minutes=discord.Embed()
                mute_minutes.add_field(name="<:yesTick:777096731438874634> Muted Member", value=f"{member.mention} was muted for {minutes} minutes and {seconds} seconds")
                await ctx.send(embed=mute_minutes)
            elif int(seconds):
                mute_seconds=discord.Embed()
                mute_seconds.add_field(name="<:yesTick:777096731438874634> Muted Member", value=f"{member.mention} was muted for {seconds} seconds")
                await ctx.send(embed=mute_seconds)

        if time and time < 300:
            await asyncio.sleep(time)
            if role in member.roles:
                await member.remove_roles(role)
                try:
                    unmuted=discord.Embed()
                    unmuted.add_field(name="<:yesTick:777096731438874634> Unmuted", value=f"You have been unmuted in {member.guild.name}")
                    await member.send(embed=unmuted)
                except discord.Forbidden:
                    return
            await self.avimetry.mutes.delete(member.id)
            try:
                self.avimetry.muted_users.pop(member.id)
            except KeyError:
                pass
    
#Unmute command
    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def unmute(self, ctx, member:discord.Member):
        role=discord.utils.get(ctx.guild.roles, name="Muted")
        if not role: 
            await ctx.send("No role named muted")
            return

        await self.avimetry.mutes.delete(member.id)
        try:
            self.avimetry.muted_users.pop(member.id)
        except KeyError:
            pass
        if role not in member.roles:
            await ctx.send("This member is not muted")
            return
        
        await member.remove_roles(role)
        await ctx.send(f"Unmuted {member.display_name}")
    
def setup(avimetry):
    avimetry.add_cog(moderation(avimetry))