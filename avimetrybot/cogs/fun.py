import discord
from discord.ext import commands
import random
import time
import asyncio
import typing
import re
import datetime

class fun(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry
        
#Magic 8 Ball
    @commands.command(aliases=['8ball', '8b'], brief="Ask a question to the magic eight ball, and you will recieve an answer")
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def eightball(self, ctx, *, question):
        responses = ["As I see it, yes.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.", "Don’t count on it.", "It is certain.", "It is decidedly so.", "Most likely.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Outlook good.", "Reply hazy, try again.", "Signs point to yes.", "Very doubtful.", "Without a doubt.", "Yes.", "Yes – definitely.", "You may rely on it.",]
        ballembed=discord.Embed(title=":8ball: Magic 8 Ball")
        ballembed.add_field(name="Question:", value=f"{question}", inline=False)
        ballembed.add_field(name="Answer:", value=f"{random.choice(responses)}", inline=False)
        await ctx.send(embed=ballembed)

#Random Number
    @commands.command(brief="Pick a random number from 1 to 100", usage="[amount]")
    async def random(self, ctx, amount: int = 100):
        x = random.randint(1, amount) 
        e = discord.Embed()
        e.add_field(name="Random Number", value=f"The number is {x}")
        await ctx.send(embed=e)

#Kill Command
    @commands.command(aliases=["murder"], brief="Kill some people. Make sure you don't get caught!")
    @commands.cooldown(5, 30, commands.BucketType.member)
    async def kill(self, ctx, member:discord.Member):
        await ctx.message.delete()
        if member == self.avimetry.user or member.bot:
            await ctx.send("You fool. Us bots can't die")
            
        else:    
            if member == ctx.author:
                await ctx.send(f"{ctx.author.mention} tried to kill themself, but your friend caught you and decided to bring you to the hospital. On the way to the hospital, your friend crashed the car. They both died.")
            else:
                kill_response=[f"**{ctx.author.display_name}** went to go kill **{member.display_name}** but when loading the gun, **{ctx.author.display_name}** shot themself in the head. **{ctx.author.display_name}** died.", 
                               f"**{ctx.author.display_name}** tried to kill **{member.display_name}** but then he remembered that **{member.display_name}** owes them money and decides to kill **{member.display_name}** later.",
                               f"**{ctx.author.display_name}** shot and killed **{member.display_name}**",
                               f"**{ctx.author.display_name}** tried to kill **{member.display_name}** by pushing them down the stairs. **{member.display_name}** called the police and the police shot and killed **{ctx.author.display_name}**.",
                               f"**{ctx.author.display_name}** tried to kill **{member.display_name}** by pushing them down the stairs. **{member.display_name}** died.",
                               f"**{ctx.author.display_name}** went to go kill **{member.display_name}** by summoning a demon, but the demon killed them both!"]
                await ctx.send(f"{random.choice(kill_response)}")

#Revive Command
    @commands.command(brief="Bring people back to life.")
    @commands.cooldown(5, 30, commands.BucketType.member)
    async def revive(self, ctx, member:discord.Member):
        await ctx.message.delete()
        if member == ctx.author:
                await ctx.send('{ctx.author.mention} has come back from the dead')      
        else:
            await ctx.send(f"{ctx.author.mention} revived {member.mention}")
            
#Say Command
    @commands.command(brief="You can make me say whatever you please!", usage="<message>")
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def say(self, ctx, *, botsay):
        await ctx.send(f'{botsay}')

#Delete Say Command
    @commands.command(brief="You can make me say whatever you please, but I delete your message so it looks like I sent it!", usage="<message>")
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
    
    @commands.group(aliases=["\U0001F36A", "kookie", "cookies"], invoke_without_command=True)
    async def cookie(self, ctx):
        cookie_menu=discord.Embed(title="Pick a difficulty", description="1️⃣ Cookie Easy\n\n2️⃣ Cookie Hard")
        cookies=await ctx.send(embed=cookie_menu)
        reactions=["1️⃣","2️⃣"]
        for reaction in reactions:
            await cookies.add_reaction(reaction)
        def check(reaction, user):
            return str(reaction.emoji) in ['1️⃣', '2️⃣'] and user != self.avimetry.user and user==ctx.author
        try:
            # pylint: disable=unused-variable
            reaction, user = await self.avimetry.wait_for('reaction_add', check=check, timeout=10)
        except asyncio.TimeoutError:
            to=discord.Embed()
            to.add_field(name=f"You took too long!", value="Timed Out.")
            await cookies.edit(embed=to)
            await cookies.clear_reactions()
        else:
            if str(reaction.emoji) == '1️⃣':
                await cookies.delete()
                cmd = self.avimetry.get_command("cookie easy")
                await cmd(ctx)
            if str(reaction.emoji) == '2️⃣':
                await cookies.delete()
                cmd = self.avimetry.get_command("cookie hard")
                await cmd(ctx)

    @cookie.command(brief="Get the cookie as fast as you can with out a countdown timer.")
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def hard(self, ctx):
        cookie_embed=discord.Embed()
        cookie_embed.add_field(name="Get the cookie!", value="Who has the fastest reaction time? Get ready to grab the cookie!")
        cd_cookie=await ctx.send(embed=cookie_embed)
        await asyncio.sleep(2)
        cookie_embed.set_field_at(0, name="Ready Up!", value=f"Get ready to get the cookie!")
        await cd_cookie.edit(embed=cookie_embed)
        await asyncio.sleep(random.randint(1,11))
        cookie_embed.set_field_at(0, name="NOW!", value="Get the cookie now!")
        await cd_cookie.edit(embed=cookie_embed)
        await cd_cookie.add_reaction("\U0001F36A")
        start=time.perf_counter()
        def check(reaction, user):
            return str(reaction.emoji) in "\U0001F36A" and user != self.avimetry.user
        try:
            # pylint: disable = unused-variable
            reaction, user = await self.avimetry.wait_for('reaction_add', check=check, timeout=10)
        except asyncio.TimeoutError:
            cookie_embed.set_field_at(0, name="Game over!", value=f"Nobody got the cookie :(")
            await cd_cookie.edit(embed=cookie_embed)
            await cd_cookie.clear_reactions()
        else:
            if str(reaction.emoji) == "\U0001F36A":
                end=time.perf_counter()
                gettime=(end-start)*1000
                total_second=f"**{round(gettime)}ms**"
                if gettime>1000:
                    gettime=gettime/1000
                    total_second=f"**{gettime:.2f}s**"
                cookie_embed.set_field_at(0, name="Good job!", value=f"{user.mention} got the cookie in **{total_second}**")
                await cd_cookie.edit(embed=cookie_embed)

    @cookie.command(brief="Get the cookie as fast as you can with a three second timer.")
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def easy(self, ctx):
        cntdown=3
        cookie_embed=discord.Embed()
        cookie_embed.add_field(name="Get the cookie!", value="Who can get the cookie the fastest? Get ready!")
        cd_cookie=await ctx.send(embed=cookie_embed)
        # pylint: disable=unused-variable
        for i in range(3):
        # pylint: enable=unused-variable
            await asyncio.sleep(1)
            cookie_embed.set_field_at(0, name="Get Ready", value=f"Get the cookie in {cntdown}")
            await cd_cookie.edit(embed=cookie_embed)
            cntdown -=1
        await asyncio.sleep(1)
        cookie_embed.set_field_at(0, name="Go!", value="Get the cookie now!")
        await cd_cookie.edit(embed=cookie_embed)
        await cd_cookie.add_reaction("\U0001F36A")
        start=time.perf_counter()
        def check(reaction, user):
            return str(reaction.emoji) in "\U0001F36A" and user != self.avimetry.user
        try:
            # pylint: disable = unused-variable
            reaction, user = await self.avimetry.wait_for('reaction_add', check=check, timeout=10)
        except asyncio.TimeoutError:
            cookie_embed.set_field_at(0, name="Game over!", value=f"Nobody got the cookie :(")
            await cd_cookie.edit(embed=cookie_embed)
            await cd_cookie.clear_reactions()
        else:
            if str(reaction.emoji) == "\U0001F36A":
                end=time.perf_counter()
                gettime=(end-start)*1000
                total_second=f"**{round(gettime)}ms**"
                if gettime>1000:
                    gettime=gettime/1000
                    total_second=f"**{gettime:.2f}s**"
                cookie_embed.set_field_at(0, name="Good job!", value=f"{user.mention} got the cookie in **{total_second}**")
                await cd_cookie.edit(embed=cookie_embed)

                
def setup(avimetry):
    avimetry.add_cog(fun(avimetry))