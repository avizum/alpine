import discord
from discord.ext import commands
import string
import random
import json
import asyncio
#event = @commands.Cog.listener
class Verification(commands.Cog, command_attrs=dict(hidden=True)):

    def __init__(self, avimetry):
        self.avimetry = avimetry

#Welcome Message
    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        global pre
        pre = prefixes[str(member.guild.id)]

        name = 'New Members'
        category = discord.utils.get(member.guild.categories, name=name)
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)
        }
        await member.guild.create_text_channel(f'{member.id}', category=category, reason = f"Started Verification for {member.name}", overwrites=overwrites)
        
        unv = member.guild.get_role(789334795100225556)
        await member.add_roles(unv)
        
        channel = discord.utils.get(self.avimetry.get_all_channels(), name=f'{member.id}')
        x=discord.Embed()
        x.add_field(name=f"Welcome to **{member.guild.name}**!", value=f"Hey, {member.mention}, welcome to **{member.guild.name}**! \n\nPlease read the rules over at the <#751967064310415360> channel. After reading the rules, come back here to start the verification process. \n\nTo start the verification process, use the command `{pre}verify` \n\nYou will be given a randomly generated code to enter in this channel.")
        await channel.send(f"{member.mention}", embed=x)
        
        y=discord.Embed()
        y.add_field(name=f"Welcome to **{member.guild.name}**!", value=f"Hey, {member.mention}, welcome to **{member.guild.name}**! \n\nPlease read the rules over at the <#751967064310415360> channel. \n\nTo start the verification process, use the command `{pre}verify` in <#{member.id}>.")
        await member.send(f"{member.mention}", embed=y)
        
#Leave Message    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        dchnl = discord.utils.get(self.avimetry.get_all_channels(), name=f'{member.id}')
        if dchnl in member.guild.channels:
            await dchnl.delete(reason=f"{member.name} left during verification process")
        else:
            channel = discord.utils.get(self.avimetry.get_all_channels(), name='joins-and-leaves')
            lm=discord.Embed()
            lm.add_field(name="Member Left", value=f"Aww, {member.mention} has left {member.guild.name}. \nThe server now has **{member.guild.member_count}** members.")
            await channel.send(embed=lm)
            

#Verify Command
    @commands.command(brief="Verify now!")
    async def verify(self, ctx):
        member = ctx.author
        role = ctx.guild.get_role(757664936548892752)        
        await ctx.message.delete()
        if role in member.roles:
            fver=discord.Embed()
            fver.add_field(name="<:aviError:777096756865269760> Already Verified", value="You are already verified!")
            await(await ctx.send(embed=fver)).delete(delay=5)
        else:
            letters = string.ascii_letters
            randomkey=(''.join(random.choice(letters) for i in range(10)))
            print(randomkey)
            if member.is_on_mobile():
                await member.send("**Here is your key. Your key will expire in 60 seconds.**")
                await member.send(f"{randomkey}")
            else:
                rkey=discord.Embed()
                rkey.add_field(name="Here is your key. Your key will expire in 60 seconds.", value=f"`{randomkey}`")
                await member.send(embed=rkey)

            ksid=discord.Embed()
            ksid.add_field(name="<:aviSuccess:777096731438874634> A key was sent to your DMs", value="Enter your key here to get verified and have access to the channels.")
            await ctx.send(embed=ksid)
            channel=ctx.channel
            def check(m):
                return m.content == randomkey and m.channel == channel
            try:
                await self.avimetry.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                if member.is_on_mobile():
                    await member.send("<:aviError:777096756865269760> **Your Key has expired**\nSorry, your key has expired. If you want to generate a new key, use the command `a.verify` to generate a new key.")
                else:
                    timeup=discord.Embed()
                    timeup.add_field(name="<:aviError:777096756865269760> Your Key has expired", value="Sorry, your key has expired. If you want to generate a new key, use the command `a.verify` to generate a new key.")
                    await ctx.author.send(embed=timeup)
            else:
                verembed=discord.Embed()
                verembed.add_field(name="<:aviSuccess:777096731438874634> Thank you", value="You have been verified!", inline=False)
                await ctx.send(embed=verembed)
                await asyncio.sleep(.5)
                await member.add_roles(role)
                await asyncio.sleep(2)
                cnl = discord.utils.get(self.avimetry.get_all_channels(),  name=f'{member.id}')
                await cnl.delete(reason=f"{member.name} finished verification")
                channel = discord.utils.get(self.avimetry.get_all_channels(),  name='joins-and-leaves')
                if channel.guild.id == ctx.author.guild.id:
                    jm=discord.Embed()
                    jm.add_field(name="Member Joined", value=f"Hey, {member.mention}, Welcome to {member.guild.name}! \nThe server now has **{member.guild.member_count}** members.")
                    await channel.send(embed=jm)
                
def setup(avimetry):
    avimetry.add_cog(Verification(avimetry))
