import discord
import time
from discord.ext import commands
import asyncio
import random
import json
import datetime
import subprocess

class Miscellaneous(commands.Cog):
    
    def __init__(self, avibot):
        self.avibot = avibot

#Ping Command
    @commands.command(brief="Gets the bot's ping.")
    async def ping(self, ctx):
        pingembed=discord.Embed()
        pingembed.add_field(name="🏓 Pong!", value=f"Bot's Ping: `{round(self.avibot.latency * 1000)}ms`")
        await ctx.send(embed=pingembed)

#Study Hall Command
    @commands.group()
    async def studyhall(self, ctx):
        if ctx.invoked_subcommand is None:
            subcn=discord.Embed(title="Command: Studyhall")
            subcn.add_field(name="Description:", value="Gives you access to the studyhall VC and channel", inline=False)
            subcn.add_field(name="Example:", value="`a.studyhall [on | off]`", inline=False)
            await ctx.send(embed=subcn)
    @studyhall.command(brief="Puts yourself in to study hall.")
    async def on(self, ctx):
        member = ctx.author
        role = discord.utils.get(member.guild.roles, name="Studying")
        role2 = discord.utils.get(member.guild.roles, name="Member")
        sho=discord.Embed()
        sho.add_field(name="Study Hall", value=f"{member.mention} is now in study hall.", inline=False)
        await ctx.send(embed=sho)
        time.sleep(0.5)
        await discord.Member.add_roles(member, role)
        await discord.Member.remove_roles(member, role2)
    @studyhall.command(brief="Removes yourself from study hall.")
    async def off(self, ctx):
        member = ctx.author
        role = discord.utils.get(member.guild.roles, name="Studying")
        role2 = discord.utils.get(member.guild.roles, name="Member")
        shof = discord.Embed()
        shof.add_field(name="Study hall", value="Now exiting study hall...")
        await ctx.send(embed=shof)
        time.sleep(0.5)
        await discord.Member.remove_roles(member, role)
        await discord.Member.add_roles(member, role2)

#Face Palm Command
    @commands.command(aliases=['fp', 'facep', 'fpalm'], brief="Hit yourself on the face!")
    async def facepalm(self, ctx):
        await ctx.send (f'{ctx.author.mention} hit their face.')

#Clean Command    
    @commands.command(brief="Grabs messages sent by me and messages that contain the command prefix and deletes them.")
    async def clean(self, ctx):
        with open("avimetry/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        pre = prefixes[str(ctx.guild.id)]
        await ctx.message.delete()
        def avibotuser(m):
            return m.author == self.avibot.user 
        def prefixmsg(m):
            return m.content.startswith(pre)  
        deleted = await ctx.channel.purge(limit=50, check=avibotuser)
        deleted2 = await ctx.channel.purge(limit=50, check=prefixmsg)
        total1=len(deleted)
        total2=len(deleted2)
        ce=discord.Embed()
        ce.add_field(name="<:aviSuccess:777096731438874634> Clean Messages",value=f"Successfully deleted **{total1}** bot messages and **{total2}** user messages")
        await ctx.send(embed=ce, delete_after=5)

#Poll command
    @commands.command(brief="Launch a poll for users to vote to.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def poll(self, ctx, question, *options: str):
        await ctx.message.delete()
        channel = self.avibot.get_channel(774075297142013972)
        if len(options) == 2 and options[0] == 'Yes' and options[1] == 'No':
            reactions = ['<:aviSuccess:777096731438874634>', '<:aviError:777096756865269760>']
        elif len(options) == 2 and options[0] == 'yes' and options[1] == 'no':
            reactions = ['<:aviSuccess:777096731438874634>', '<:aviError:777096756865269760>']
        else:
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        description = []
        for x, option in enumerate(options):
            description +='\n\n {} {}'.format(reactions[x], option)
        embed = discord.Embed(title=question, description=''.join(description))
        embed.set_footer(text=f"Poll from: {ctx.author.name}#{ctx.author.discriminator}")
        react_message = await channel.send(embed=embed)
        for reaction in reactions[:len(options)]:
            await react_message.add_reaction(reaction)

    #Request Nick command
    @commands.command(brief="Requests a new nick name.")
    async def requestnick(self, ctx, rqnick):
        channels = self.avibot.get_channel(787942179310010368)
        rq=discord.Embed()
        rq.add_field(name="Request Nickname", value=f"Your request has been sent. \nRequested Nickname: `{rqnick}`")
        ap=discord.Embed()
        ap.add_field(name="Incoming Request", value=f"{ctx.author.mention} requested to change their nickname to `{rqnick}` \nIf you want to change their nickname, use the command below to change their nickname \n`a.cnick {ctx.author.id} {rqnick}`")
        await ctx.send(embed=rq, delete_after=5)
        await channels.send(embed=ap)

    @commands.command(brief="Gets a member's information", enabled=False)
    async def info(self, ctx, *, member : discord.Member):
        ie = discord.Embed(title="User Info", description=f"User Information for {member.mention}:\n\n **Username:** {member.name}#{member.discriminator}\n**Nickname:** {member.nick}\n **Join Date:** {member.joined_at}\n**Roles** {member.roles}",timestamp=datetime.datetime.utcnow())
        ie.set_thumbnail(url=member.avatar_url)
        ie.add_field(name="Server Permissions", value="permissions")
        await ctx.send(embed=ie)

    @commands.command()
    @commands.is_owner()
    async def pull(self, ctx):
        command = 'git clone git@github.com:jbkn/avimetry'
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        print(output, error)
        await ctx.send(f"`output`")
        

def setup(avibot):
    avibot.add_cog(Miscellaneous(avibot))


