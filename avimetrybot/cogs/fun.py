import discord
from discord.ext import commands
import random
import time
import asyncio
import json
import typing

class Fun(commands.Cog):
    
    def __init__(self, avimetry):
        self.avimetry = avimetry
        
#Magic 8 Ball
    @commands.command(aliases=['8ball', '8b'], brief="Ask a question to the magic eight ball, and you will recieve an answer")
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def eightball(self, ctx, *, question):
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        global pre
        pre = prefixes[str(ctx.guild.id)]
        responses = ["As I see it, yes.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.", "Don’t count on it.", "It is certain.", "It is decidedly so.", "Most likely.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Outlook good.", "Reply hazy, try again.", "Signs point to yes.", "Very doubtful.", "Without a doubt.", "Yes.", "Yes – definitely.", "You may rely on it.",]
        ballembed=discord.Embed(title=":8ball: Magic 8 Ball")
        ballembed.add_field(name="Question:", value=f"{question}", inline=False)
        ballembed.add_field(name="Answer:", value=f"{random.choice(responses)}", inline=False)
        await ctx.send(embed=ballembed)

#Random Number
    @commands.group(brief="Pick a random number from 1 to 100")
    async def random(self, ctx, amount: int = 100):
        x = random.randint(1, amount) 
        e = discord.Embed()
        e.add_field(name="Random Number", value=f"The number is {x}")
        await ctx.send(embed=e)

#Kill Command
    @commands.command(aliases=["murder"], brief="Kill some people. Make sure you don't get caught!")
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def kill(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if member == self.avimetry.user or member.bot:
            a = discord.Embed(description="You fool. Us bots can't die",)
            await ctx.send(embed=a)
            
        else:    
            if member == ctx.author:
                await ctx.send(f"{ctx.author.mention} tried to kill themself, but your friend caught you and decided to bring you to the hospital. On the way to the hospital, your friend crashed the car. They both died.")
            else:
                kill_response=[f"**{ctx.author.display_name}** went to go kill **{member.display_name}** but when loading the gun, but **{ctx.author.display_name}** they shot themselves. They died.", 
                               f"**{ctx.author.display_name}** tried to kill **{member.display_name}** but then he remembered that **{member.display_name}** owes them money and decides to kill them later.",
                               f"**{ctx.author.display_name}** shot and killed **{member.display_name}**",
                               f"**{ctx.author.display_name}** tried to kill **{member.display_name}** by pushing them down the stairs. They called the police and the police shot and killed you.",
                               f"**{ctx.author.display_name}** tried to kill **{member.display_name}** by pushing them down the stairs. They died."]
                await ctx.send(f"{random.choice(kill_response)}")

#Revive Command
    @commands.command(brief="Bring people back to life.")
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def revive(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if member == ctx.author:
                await ctx.send('{ctx.author.mention} has come back from the dead')      
        else:
            await ctx.send(description=f"{ctx.author.mention} revived {member.mention}")
            
#Say Command
    @commands.command(brief="You can make me say whatever you please!")
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def say(self, ctx, *, botsay):
        await ctx.send(f'{botsay}')

#Delete Say Command
    @commands.command(brief="You can make me say whatever you please, but I delete your message so it looks like I sent it!")
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def dsay(self, ctx, *, dbotsay):
        await ctx.message.delete()
        await ctx.send(f'{dbotsay}')

#Skin Command
    @commands.command(brief="Remove the skin off of people that you don't like.")
    async def skin(self, ctx, member:discord.Member):
        await ctx.message.delete()
        if member == ctx.author:
            c = discord.Embed(description="You can't skin yourself, stupid")
            await ctx.send(embed=c)
        else:
            e = discord.Embed(description=f'{member.mention} was skinned.')
            await ctx.send(embed=e)

    @commands.command(aliases=['sd'], brief="Self destruct? Who put that button there?")
    async def selfdestruct(self, ctx):
        a = discord.Embed(description=f"{ctx.author.mention} self destructed due to overloaded fuel canisters")
        await ctx.send(embed=a)

    @commands.command(brief="Drop kicks someone")
    async def dropkick(self, ctx, *, mention:discord.Member):
        if mention == ctx.author:
            a = discord.Embed(description=f"{ctx.author.mention} tried dropkicking themselves")
            await ctx.send(embed=a)
        else:
            b = discord.Embed(description=f'{ctx.author.mention} dropkicked {mention.mention}')
            await ctx.send(embed=b)

    #Face Palm Command
    @commands.command(aliases=['fp', 'facep', 'fpalm'], brief="Hit yourself on the face!")
    async def facepalm(self, ctx):
        a = discord.Embed(description=f'{ctx.author.mention} hit their face.')
        await ctx.send(embed=a)
    
def setup(avimetry):
    avimetry.add_cog(Fun(avimetry))