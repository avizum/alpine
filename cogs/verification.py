import discord
from discord.ext import commands
import string
import random
import json
import asyncio
#event = @commands.Cog.listener
class Verification(commands.Cog):

    def __init__(self, avibot):
        self.avibot = avibot

#Welcome Message
    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open("avimetry/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        global pre
        pre = prefixes[str(member.guild.id)]

        if member.guild.id != 751490725555994716:
            return
        else:
            channel = discord.utils.get(self.avibot.get_all_channels(),  name='joins-and-leaves')
            jm=discord.Embed()
            jm.add_field(name="Member Joined", value=f"Hey, {member.mention}, Welcome to {member.guild.name}! \nThe server now has **{member.guild.member_count}** members.")
            await channel.send(embed=jm)
            
            wegipii=discord.Embed()
            wegipii.add_field(name=f"Welcome to **{member.guild.name}**!", value=f"Hey, {member.mention}, welcome to the server! \nPlease read the rules over at the <#751967064310415360> channel. After reading the rules, come back here to start the verification process. \nTo start the verification process, use the command `{pre}verify`. \nYou will be given a randomly generated code to enter in the <#767651584254410763> channel.")
            await member.send(f"{member.mention}", embed=wegipii)
            
            unv = member.guild.get_role(789334795100225556)
            await member.add_roles(unv)
#Leave Message    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != 751490725555994716:
            return
        channel = discord.utils.get(self.avibot.get_all_channels(),  name='joins-and-leaves')
        lm=discord.Embed()
        lm.add_field(name="Member Left", value=f"Aww, {member.mention} has left {member.guild.name}. \nThe server now has **{member.guild.member_count}** members.")
        await channel.send(embed=lm)

#Auto-Delete Message
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avibot.user:
            return
        if message.channel == discord.utils.get(self.avibot.get_all_channels(), name='verify'):
            if message.content.startswith('a.v'):
                return
            else: 
                await message.delete(delay=1)

#Verify Command
    @commands.command(brief="Verify now!")
    async def verify(self, ctx):
        member = ctx.author
        role = ctx.guild.get_role(757664936548892752)
        unv = ctx.guild.get_role(789334795100225556)
        await ctx.message.delete()
        if role in member.roles:
            fver=discord.Embed()
            fver.add_field(name="<:aviError:777096756865269760> Already Verified", value="You are already verified!")
            await(await ctx.send(embed=fver)).delete(delay=5)
        else:
            letters = string.ascii_letters
            randomkey=(''.join(random.choice(letters) for i in range(10)))
            rkey=discord.Embed()
            rkey.add_field(name="Here is your key. Your key will expire in 60 seconds.", value=f"`{randomkey}`")
            print(randomkey)
            await ctx.author.send(embed=rkey)
            ksid=discord.Embed()
            ksid.add_field(name="<:aviSuccess:777096731438874634> A key was sent to your DMs", value="Enter your key here to get verified and have access to the channels.")
            codemessage = await ctx.send(embed=ksid, delete_after=60)

            channel=ctx.channel
                
            def check(m):
                return m.content == randomkey and m.channel == channel
            try:
                await self.avibot.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                timeup=discord.Embed()
                timeup.add_field(name="<:aviError:777096756865269760> Your Key has expired", value="Sorry, your key has expired. If you want to generate a new key, use the command `a.verify` to generate a new key.")
                await ctx.author.send(embed=timeup)
            else:
                verembed=discord.Embed()
                verembed.add_field(name="<:aviSuccess:777096731438874634> Thank you", value="You have been verified!", inline=False)
                await ctx.send(embed=verembed, delete_after=5)
                await asyncio.sleep(.5)
                await member.add_roles(role)
                await member.remove_roles(unv)
                await asyncio.sleep(2)
                await codemessage.delete()

def setup(avibot):
    avibot.add_cog(Verification(avibot))
