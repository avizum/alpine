import discord
from discord.ext import commands
import random
import time
import asyncio
import json
import datetime


class Moderation(commands.Cog):
    
    def __init__(self, avibot):
        self.avibot = avibot
        self.lockchannel=False

#Purge Command
    @commands.command(brief="Delete a number of messages in the current channel.")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        await ctx.message.delete()
        if amount == 0:
            pass
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

    @purge.error
    async def purgeErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            purgeusage=discord.Embed(title="Command: Purge")
            purgeusage.add_field(name="Description: ", value="Delete a number of messages in the current channel", inline=False)
            purgeusage.add_field(name="Example:", value="`a.purge [amount]`", inline=False)
            await ctx.send(embed=purgeusage)

#Lock Channel Command

    @commands.command(brief="Locks the mentioned channel.", timestamp=datetime.datetime.utcnow())
    @commands.has_permissions(manage_messages=True)
    async def lock(self, ctx, channel : discord.TextChannel, *, reason):
        await channel.set_permissions(ctx.guild.default_role, send_messages=False, read_messages=False)
        lc=discord.Embed()
        lc.add_field(name=":lock: Channel has been locked.", value=f"{ctx.author.mention} has locked down <#{channel.id}> with the reason of {reason}. Only Staff members can speak now.")
        await channel.send(embed=lc)
    @lock.error
    async def lockErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            lmra=discord.Embed(title="Command: Lock")
            lmra.add_field(name="Description", value="Locks the mentioned channel.", inline=False)
            lmra.add_field(name="Example:", value="a.lock [#channel]", inline=False)
            await ctx.send(embed=lmra)

#Unlock Channel command
    @commands.command(brief="Unlocks the mentioned channel.", timestamp=datetime.datetime.utcnow())
    @commands.has_permissions(manage_messages=True)
    async def unlock(self, ctx, channel : discord.TextChannel, *, reason):
        await channel.set_permissions(ctx.guild.default_role, send_messages=None, read_messages=False)
        uc=discord.Embed()
        uc.add_field(name=":unlock: Channel has been unlocked.", value=f"{ctx.author.mention} has unlocked <#{channel.id}> with the reason of {reason}. Everyone can speak now.")
        await channel.send(embed=uc)
    
    @unlock.error
    async def unlockErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            ulmra=discord.Embed(title="Command: Unlock")
            ulmra.add_field(name="Description", value="Unlocks the mentioned channel.", inline=False)
            ulmra.add_field(name="Example:", value="a.unlock [#channel]", inline=False)
            await ctx.send(embed=ulmra)

#Kick Command
    @commands.command(brief="Kicks a member from the server.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member : discord.Member, *, reason):
        if member==ctx.message.author:
            mecma=discord.Embed()
            mecma.add_field(name="<:aviError:777096756865269760> No Permission", value="You can't kick yourself. That's just stupid.")
            await ctx.send(embed=mecma)
        elif member==self.avibot.user:
            msau=discord.Embed()
            msau.add_field(name="<:aviError:777096756865269760> No Permission", value="You can't kick me, because that won't work.")
            await ctx.send(embed=msau)
        elif member.top_role > ctx.author.top_role:
            mtrgratr=discord.Embed()
            mtrgratr.add_field(name="<:aviError:777096756865269760> No Permission", value="You can not kick someone that has a higher role than you. They must have a role under you.", inline=False)
            await ctx.send(embed=mtrgratr)
        elif member.top_role== ctx.author.top_role:
            mtretatr=discord.Embed()
            mtretatr.add_field(name="<:aviError:777096756865269760> No Permission", value="You can not kick someone that has the same role as you. They must have a role under you.", inline=False)
            await ctx.send(embed=mtretatr)
        else:
            await member.kick(reason=reason)
            kickembed=discord.Embed()
            kickembed.add_field(name="<:aviSuccess:777096731438874634> Kick Member", value=f"**{member}** has been kicked from the server.", inline=False)
            await ctx.send(embed=kickembed)
    @kick.error
    async def kickErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            kickusage=discord.Embed(title="Command: Kick")
            kickusage.add_field(name="Description: ", value="Kicks a member from the server.", inline=False)
            kickusage.add_field(name="Example:", value="`a.kick [@Member] [Reason]`", inline=False)
            await ctx.send(embed=kickusage)
#Ban Command
    @commands.command(brief="Bans a member from the server")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member : discord.Member, *, reason):
        if member==ctx.message.author:
                mecma=discord.Embed()
                mecma.add_field(name="<:aviError:777096756865269760> No Permission", value="You can't ban yourself. That's just stupid.")
                await ctx.send(embed=mecma)
        elif member==self.avibot.user:
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
    @ban.error
    async def banErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            banusage=discord.Embed(title="Command: Ban")
            banusage.add_field(name="Description:", value="Bans a member from the server", inline=False)
            banusage.add_field(
                name="Example:", value="`a.ban [@Member] [reason]`", inline=False)
            await ctx.send(embed=banusage)

#Unban Command
    @commands.command(brief="Unbans a member from the server.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, userid):
        some_member = discord.Object(id=userid)
        await ctx.guild.unban(some_member)
        unbanenmbed=discord.Embed()
        unbanenmbed.add_field(name="<:aviSuccess:777096731438874634> Unban Member", value=f"Unbanned <@{userid}> ({userid}) from **{ctx.guild.name}**.", inline=False)
        await ctx.send(embed=unbanenmbed)
    @unban.error
    async def unbanErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            unbanusage=discord.Embed(title="Command: Unban")
            unbanusage.add_field(name="Description:", value="Unbans a member from the server", inline=False)
            unbanusage.add_field(name="Example:", value="`a.unban [user#discriminator]`", inline=False)
            await ctx.send(embed=unbanusage)

#CNick Command
    @commands.command(brief="Changes a member's nickname.")
    @commands.has_permissions(kick_members=True)
    async def cnick(self, ctx, member: discord.Member, *,nick):
        oldnick=member.display_name
        await member.edit(nick=nick)
        newnick=member.display_name
        nickembed=discord.Embed(title="<:aviSuccess:777096731438874634> Nickname Changed")
        nickembed.add_field(name="Old Nickname", value=f"{oldnick}", inline=True)
        nickembed.add_field(name="New Nickname", value=f"{newnick}", inline=True)
        await ctx.send(embed=nickembed)
    @cnick.error
    async def cnickErr(self, ctx, error):

        if isinstance(error, commands.MissingRequiredArgument):
            cnickusage=discord.Embed(title="Command: CNick")
            cnickusage.add_field(name="Description:", value="Changes a member's nickname", inline=False)
            cnickusage.add_field(name="Example:", value="`a.cnick [@Member] [NewNickname]`", inline=False)
            await ctx.send(embed=cnickusage)

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
    @rnick.error
    async def rnickErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            rnu=discord.Embed(title="Command: RNick")
            rnu.add_field(name="Description:", value="Restores a member's nick name to their username.", inline=False)
            rnu.add_field(name="Example:", value="`a.rnick [@Member]`")
            await ctx.send(embed=rnu)
    
#Slowmode Command
    @commands.command(brief="Sets the slowmode in the current channel.")
    @commands.has_permissions(manage_guild=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        smembed=discord.Embed()
        smembed.add_field(name="<:aviSuccess:777096731438874634> Set Slowmode", value=f"Slowmode delay is now set to {seconds} seconds.")
        await ctx.send(embed=smembed)
    @slowmode.error
    async def slowmodeErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            print("sad")
#Role Command
    @commands.command(brief="Gives or removes a role from a member.")
    @commands.has_permissions(kick_members=True)
    async def role(self, ctx, member:discord.Member, addremove, role:discord.Role):#, *, reason="No Reason was provided."):
        if addremove == ["+", " +", "+ "]:
            await ctx.send("added")
        elif addremove == '-':
            await ctx.send("removed")  
    @role.error
    async def roleErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            print("sad")
    
#mute command
    @commands.command(brief="Mutes a member.")
    @commands.has_permissions(kick_members=True)
    async def mute(self, ctx, member : discord.Member):
        role2 = discord.utils.get(ctx.guild.roles, name="Muted")
        await ctx.member.add_roles(member, role2)
        await ctx.send(f"muted {member}")
#292 lines before
def setup(avibot):
    avibot.add_cog(Moderation(avibot))