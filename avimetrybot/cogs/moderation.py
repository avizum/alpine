import discord
from discord.ext import commands
import random
import time
import asyncio
import json
import datetime


class Moderation(commands.Cog):
    
    def __init__(self, avimetry):
        self.avimetry = avimetry
        
#Purge Command
    @commands.command(brief="Delete a number of messages in the current channel.")
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(5, 300, commands.BucketType.member)
    async def purge(self, ctx, amount: int):
        await ctx.message.delete()
        if amount == 0:
            pass
        elif amount > 100:
            a100=discord.Embed()
            a100.add_field(name="<:aviError:777096756865269760> No Permission", value="You can't purge more than 100 messages at a time.")
            await ctx.send(embed=a100, delete_after=10)
        else:
            authors = {}
            async for message in ctx.channel.history(limit=amount):
                if message.author not in authors:
                    authors[message.author] = 1
                else:
                    authors[message.author] += 1
            await asyncio.sleep(.1)
            await ctx.channel.purge(limit=amount)   
            msg = "\n".join([f"{author}: {amount}" for author, amount in authors.items()])

            pe=discord.Embed()
            pe.add_field(name="<:aviSuccess:777096731438874634> Purge Messages", value=f"Here are the results of the purged messages:\n`{msg}`")
            pe.set_footer(text="This message will be deleted in 15 seconds.")
            await ctx.send(embed=pe, delete_after=15)

#Lock Channel Command
    @commands.command(brief="Locks the mentioned channel.", timestamp=datetime.datetime.utcnow())
    @commands.has_permissions(manage_messages=True)
    async def lock(self, ctx, channel : discord.TextChannel, *, reason):
        await channel.set_permissions(ctx.guild.default_role, send_messages=False, read_messages=False)
        lc=discord.Embed()
        lc.add_field(name=":lock: Channel has been locked.", value=f"{ctx.author.mention} has locked down <#{channel.id}> with the reason of {reason}. Only Staff members can speak now.")
        await channel.send(embed=lc)

#Unlock Channel command
    @commands.command(brief="Unlocks the mentioned channel.", timestamp=datetime.datetime.utcnow())
    @commands.has_permissions(manage_messages=True)
    async def unlock(self, ctx, channel : discord.TextChannel, *, reason):
        await channel.set_permissions(ctx.guild.default_role, send_messages=None, read_messages=False)
        uc=discord.Embed()
        uc.add_field(name=":unlock: Channel has been unlocked.", value=f"{ctx.author.mention} has unlocked <#{channel.id}> with the reason of {reason}. Everyone can speak now.")
        await channel.send(embed=uc)
    
#Kick Command
    @commands.command(brief="Kicks a member from the server.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member : discord.Member, *, reason = "No reason was provided"):
        if member==ctx.message.author:
            e1=discord.Embed()
            e1.add_field(name="<:aviError:777096756865269760> No Permission", value="You can't kick yourself. That's just stupid.")
            await ctx.send(embed=e1, delete_after=10)
        elif member==self.avimetry.user:
            e2=discord.Embed()
            e2.add_field(name="<:aviError:777096756865269760> No Permission", value="You can't kick me, because that won't work.")
            await ctx.send(embed=e2, delete_after=10)
        elif member.top_role > ctx.author.top_role:
            e3=discord.Embed()
            e3.add_field(name="<:aviError:777096756865269760> No Permission", value="You can not kick someone that has a higher role than you. They must have a role under you.", inline=False)
            await ctx.send(embed=e3, delete_after=10)
        elif member.top_role== ctx.author.top_role:
            e4=discord.Embed()
            e4.add_field(name="<:aviError:777096756865269760> No Permission", value="You can not kick someone that has the same role as you. They must have a role under you.", inline=False)
            await ctx.send(embed=e4, delete_after=10)
        else:
            bae=discord.Embed(title=f"You have been kicked from {ctx.guild.name}", timestamp=datetime.datetime.utcnow())
            bae.add_field(name= "Moderator:", value=f"{ctx.author.mention} \n`{ctx.author.id}`")
            bae.add_field(name="Reason:", value=f"{reason}")
            await member.send(embed=bae)
            await member.kick(reason=reason)
            kickembed=discord.Embed()
            kickembed.add_field(name="<:aviSuccess:777096731438874634> Kick Member", value=f"**{member}** has been kicked from the server.", inline=False)
            await ctx.send(embed=kickembed)

#Ban Command
    @commands.command(brief="Bans a member from the server")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member : discord.Member, *, reason = "No reason was provided"):
        if member==ctx.message.author:
                mecma=discord.Embed()
                mecma.add_field(name="<:aviError:777096756865269760> No Permission", value="You can't ban yourself. That's just stupid.")
                await ctx.send(embed=mecma)
        elif member==self.avimetry.user:
                msau=discord.Embed()
                msau.add_field(name="<:aviError:777096756865269760> No Permission", value="You can't ban me, because that won't work.")
                await ctx.send(embed=msau)
        elif member.top_role > ctx.author.top_role:
                mtrgratr=discord.Embed()
                mtrgratr.add_field(name="<:aviError:777096756865269760> No Permission", value="You can not ban someone that has a higher role than you. They must have a role under you.", inline=False)
                await ctx.send(embed=mtrgratr)
        elif member.top_role== ctx.author.top_role:
            mtretatr=discord.Embed()
            mtretatr.add_field(name="<:aviError:777096756865269760> No Permission", value="You can not ban someone that has the same role as you. They must have a role under you.", inline=False)
            await ctx.send(embed=mtretatr)
        else:
            bae=discord.Embed(title=f"You have been banned from {ctx.guild.name}", timestamp=datetime.datetime.utcnow())
            bae.add_field(name= "Moderator:", value=f"{ctx.author.mention} \n`{ctx.author.id}`")
            bae.add_field(name="Reason:", value=f"{reason}")
            await member.send(embed=bae)
            await asyncio.sleep(.5)
            await member.ban(reason=reason)
            banembed=discord.Embed()
            banembed.add_field(name="<:aviSuccess:777096731438874634> Ban Member", value=f"{member.mention} (`{member.id}`) has been banned from **{ctx.guild.name}**.", inline=False)
            await ctx.send(embed=banembed)

#Unban Command
    @commands.command(brief="Unbans a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, userid):
        some_member = discord.Object(id=userid)
        await ctx.guild.unban(some_member)
        unbanenmbed=discord.Embed()
        unbanenmbed.add_field(name="<:aviSuccess:777096731438874634> Unban Member", value=f"Unbanned <@{userid}> ({userid}) from **{ctx.guild.name}**.", inline=False)
        await ctx.send(embed=unbanenmbed)

#CNick Command
    @commands.command(brief="Changes a member's nickname.")
    @commands.has_permissions(kick_members=True)
    async def cnick(self, ctx, member: discord.Member, *,nick):
        if ctx.channel.id != 787942179310010368:
            await ctx.send("This command can only be used in <#787942179310010368>.")
        else:
            oldnick=member.display_name
            await member.edit(nick=nick)
            newnick=member.display_name
            nickembed=discord.Embed(title="<:aviSuccess:777096731438874634> Nickname Changed")
            nickembed.add_field(name="Old Nickname", value=f"{oldnick}", inline=True)
            nickembed.add_field(name="New Nickname", value=f"{newnick}", inline=True)
            await ctx.send(embed=nickembed)

#RNick Command
    @commands.command(brief="Restores a member's nick name to their username.")
    @commands.has_permissions(kick_members=True)
    async def rnick(self, ctx, member: discord.Member):
        nick=member.name
        oldnick=member.display_name
        await member.edit(nick=nick)
        newnick=member.display_name
        nickembed=discord.Embed(title="<:aviSuccess:777096731438874634> Restored Nickname")
        nickembed.add_field(name="Old Nickname", value=f"{oldnick}", inline=True)
        nickembed.add_field(name="New Nickname", value=f"{newnick}", inline=True)
        await ctx.send(embed=nickembed)

#Slowmode Command
    @commands.command(brief="Sets the slowmode in the current channel.")
    @commands.has_permissions(manage_guild=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        smembed=discord.Embed()
        smembed.add_field(name="<:aviSuccess:777096731438874634> Set Slowmode", value=f"Slowmode delay is now set to {seconds} seconds.")
        await ctx.send(embed=smembed)

#Role Command
    @commands.command(brief="Gives or removes a role from a member.")
    @commands.has_permissions(kick_members=True)
    async def role(self, ctx, member:discord.Member, addremove, role:discord.Role):#, *, reason="No Reason was provided."):
        if addremove == ["+", " +", "+ "]:
            await ctx.send("added")
        elif addremove == '-':
            await ctx.send("removed")  
    
#mute command
    @commands.command(brief="Mutes a member.")
    @commands.has_permissions(kick_members=True)
    async def mute(self, ctx, member : discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        await ctx.member.add_roles(role)
        await ctx.send(f"muted {member}")

def setup(avimetry):
    avimetry.add_cog(Moderation(avimetry))