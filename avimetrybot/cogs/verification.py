import discord
from discord.ext import commands
import string
import random
import json
import asyncio
#event = @commands.Cog.listener
class Verification(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry

#Welcome Message
    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        global pre
        pre = prefixes[str(member.guild.id)]

        with open("./avimetrybot/files/verification.json", "r") as f:
            vergate = json.load(f)
        if str(member.guild.id) in vergate:
            if vergate[str(member.guild.id)] == False:
                return
            elif vergate[str(member.guild.id)] == True:
                name = 'New Members'
                category = discord.utils.get(member.guild.categories, name=name)
                overwrites = {
                    member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    member: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)
                }
                await member.guild.create_text_channel(f'{member.id}', category=category, reason = f"Started Verification for {member.name}", overwrites=overwrites)
                
                channel = discord.utils.get(self.avimetry.get_all_channels(), name=f'{member.id}')
                x=discord.Embed()
                x.add_field(name=f"Welcome to **{member.guild.name}**!", value=f"Hey, {member.mention}, welcome to **{member.guild.name}**! \n\nPlease read the rules over at the rules channel. After reading the rules, come back here to start the verification process. \n\nTo start the verification process, use the command `{pre}verify` \n\nYou will be given a randomly generated code to enter in this channel. **If you are on mobile, Please set your status to anything but `INVISIBLE`**")
                await channel.send(f"{member.mention}", embed=x)
                try:
                    y=discord.Embed()
                    y.add_field(name=f"Welcome to **{member.guild.name}**!", value=f"Hey, {member.mention}, welcome to **{member.guild.name}**! \n\nPlease read the rules over at the rules channel. \n\nTo start the verification process, use the command `{pre}verify` in <#{channel.id}>.")
                    await member.send(f"{member.mention}", embed=y)
                except discord.Forbidden:
                    return
                
#Leave Message    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        dchnl = discord.utils.get(self.avimetry.get_all_channels(), name=f'{member.id}')
        if dchnl in member.guild.channels:
            await dchnl.delete(reason=f"{member.name} left during verification process")
        else:
            channel = discord.utils.get(self.avimetry.get_all_channels(), name='joins-and-leaves')
            if member.guild.id == channel.guild.id:
                lm=discord.Embed()
                lm.add_field(name="Member Left", value=f"Aww, {member.mention} has left {member.guild.name}. \nThe server now has **{member.guild.member_count}** members.")
                await channel.send(embed=lm)


    @commands.command(aliases=["vgate", "vergate"])
    @commands.has_permissions(administrator=True)
    async def verificationgate(self, ctx, option):
        if option.lower() == "true":
            with open("./avimetrybot/files/verification.json", "r") as f:
                vergate = json.load(f)
            vergate[str(ctx.guild.id)] = True
            with open("./avimetrybot/files/verification.json", "w") as f:
                json.dump(vergate, f, indent=4)
            enabled=discord.Embed()
            enabled.add_field(name="<:yesTick:777096731438874634> Verification Gate", value="Verification gate is set to `true`")
            await ctx.send(embed=enabled)
        if option.lower() == "false":
            with open("./avimetrybot/files/verification.json", "r") as f:
                vergate = json.load(f)
            vergate[str(ctx.guild.id)] = False
            with open("./avimetrybot/files/verification.json", "w") as f:
                json.dump(vergate, f, indent=4)
            disabled=discord.Embed()
            disabled.add_field(name="<:yesTick:777096731438874634> Verification Gate", value="Verification gate is set to `false`")
            await ctx.send(embed=disabled)

            

#Verify Command
    @commands.command(brief="Verify now!")
    async def verify(self, ctx):
        member = ctx.author
        role = discord.utils.get(ctx.guild.roles, name='Member')
     
        await ctx.message.delete()
        if role in member.roles:
            fver=discord.Embed()
            fver.add_field(name="<:noTick:777096756865269760> Already Verified", value="You are already verified!")
            await(await ctx.send(embed=fver)).delete(delay=5)
        else:
            letters = string.ascii_letters
            randomkey=(''.join(random.choice(letters) for i in range(10)))
            if member.is_on_mobile():
                try:
                    await member.send("**Here is your key. Your key will expire in 60 seconds.**")
                    await member.send(f"{randomkey}")
                except discord.Forbidden:
                    keyforbidden=discord.Embed()
                    keyforbidden.add_field(name="Please turn on your DMs and run the `verify` command again.", value=f"User Settings > Privacy & Safety > Allow direct messages from server members")
                    await ctx.send(embed=keyforbidden)
                    return
            else:
                try:
                    rkey=discord.Embed()
                    rkey.add_field(name="Here is your key. Your key will expire in 60 seconds.", value=f"`{randomkey}`")
                    await member.send(embed=rkey)
                except discord.Forbidden:
                    keyforbidden=discord.Embed()
                    keyforbidden.add_field(name="Please turn on your DMs and run the `verify` command again.", value=f"User Settings > Privacy & Safety > Allow direct messages from server members")
                    await ctx.send(embed=keyforbidden)
                    return

            ksid=discord.Embed()
            ksid.add_field(name="<:yesTick:777096731438874634> A key was sent to your DMs", value="Enter your key here to get verified and have access to the channels.")
            await ctx.send(embed=ksid)
            channel=ctx.channel
            def check(m):
                return m.content == randomkey and m.channel == channel
            try:
                await self.avimetry.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                if member.is_on_mobile():
                    await member.send("<:noTick:777096756865269760> **Your Key has expired**\nSorry, your key has expired. If you want to generate a new key, use the command `a.verify` to generate a new key.")
                else:
                    timeup=discord.Embed()
                    timeup.add_field(name="<:noTick:777096756865269760> Your Key has expired", value="Sorry, your key has expired. If you want to generate a new key, use the command `a.verify` to generate a new key.")
                    await ctx.author.send(embed=timeup)
            else:
                verembed=discord.Embed()
                verembed.add_field(name="<:yesTick:777096731438874634> Thank you", value="You have been verified!", inline=False)
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
