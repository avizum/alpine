import discord
from discord.ext import commands
import random
import time
import asyncio
import json

class Fun(commands.Cog):
    
    def __init__(self, avibot):
        self.avibot = avibot

#Magic 8 Ball
    @commands.command(aliases=['8ball', '8b'], brief="Ask a question to the magic eight ball, and you will recieve an answer")
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def eightball(self, ctx, *, question):
        with open("files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        global pre
        pre = prefixes[str(ctx.guild.id)]
        responses = ["As I see it, yes.", "Ask again later.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.", "Don’t count on it.", "It is certain.", "It is decidedly so.", "Most likely.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Outlook good.", "Reply hazy, try again.", "Signs point to yes.", "Very doubtful.", "Without a doubt.", "Yes.", "Yes – definitely.", "You may rely on it.",]
        ballembed=discord.Embed(title=":8ball: Magic 8 Ball")
        ballembed.add_field(name="Question:", value=f"{question}", inline=False)
        ballembed.add_field(name="Answer:", value=f"{random.choice(responses)}", inline=False)
        await ctx.send(embed=ballembed)

#Roll Dice
    @commands.group(brief="Roll a dice!")
    async def roll(self, ctx):
        if ctx.invoked_subcommand is None:
            rollembed=discord.Embed(title="Command: a.roll", description="There are different types of die you can choose from. Check below.")
            rollembed.add_field(name="Four Sided", value="`a.roll d4`", inline=True)
            rollembed.add_field(name="Six Sided ", value="`a.roll d6`", inline=True)
            rollembed.add_field(name="Eight Sided", value="`a.roll d8`", inline=True)
            rollembed.add_field(name="Ten Sided", value="`a.roll d10`", inline=True)
            rollembed.add_field(name="Twelve Sided", value="`a.roll d12`", inline=True)
            rollembed.add_field(name="Twenty Sided", value="`a.roll d20`", inline=True)
            await ctx.send(embed=rollembed)
    @roll.command(brief="Roll a 4 sided dice")
    async def d4(self, ctx):
        d4responses = ['1','2','3','4']
        d4embed=discord.Embed()
        d4embed.add_field(name="🎲 Roll Dice", value=f"I rolled a **{random.choice(d4responses)}**!", inline=False)
        await ctx.send(embed=d4embed)
    @roll.command(brief="Roll a 6 sided dice")
    async def d6(self, ctx):
        d6responses = ['1','2','3','4','5','6',]
        d6embed=discord.Embed()
        d6embed.add_field(name="🎲 Roll Dice", value=f"I rolled a **{random.choice(d6responses)}**!", inline=False)
        await ctx.send(embed=d6embed)
    @roll.command(brief="Roll an 8 sided dice")
    async def d8(self, ctx):
        d8responses = ['1','2','3','4','5','6','7','8']   
        d8embed=discord.Embed()
        d8embed.add_field(name="🎲 Roll Dice", value=f"I rolled a **{random.choice(d8responses)}**!", inline=False)
        await ctx.send(embed=d8embed)
    @roll.command(brief="Roll a 10 sided dice")
    async def d10(self, ctx):
        d10responses = ['1','2','3','4','5','6','7','8','10']
        d10embed=discord.Embed()
        d10embed.add_field(name="🎲 Roll Dice", value=f"I rolled a **{random.choice(d10responses)}**!", inline=False)
        await ctx.send(embed=d10embed)   
    @roll.command(brief="Roll a 12 sided dice")
    async def d12(self, ctx):
        d12responses = ['1','2','3','4','5','6','7','8','10','11','12']
        d12embed=discord.Embed()
        d12embed.add_field(name="🎲 Roll Dice", value=f"I rolled a **{random.choice(d12responses)}**!", inline=False)
        await ctx.send(embed=d12embed)
    @roll.command(brief="Roll a 20 sided dice") 
    async def d20(self, ctx):
        d20responses = ['1','2','3','4','5','6','7','8','10','11','12','13','14','15','16','17','18','19','20']
        d20embed=discord.Embed()
        d20embed.add_field(name="🎲 Roll Dice", value=f"I rolled a **{random.choice(d20responses)}**!", inline=False)
        await ctx.send(embed=d20embed)

#Kill Command
    @commands.command(aliases=["murder"], brief="Kill some people. Make sure you don't get caught!")
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def kill(self, ctx, member: discord.Member):
        await ctx.message.delete()
        role = discord.utils.get(member.guild.roles, name='Dead')
        if member == self.avibot.user:
            a = discord.Embed(description="'You fool. I can not die. Now **YOU MUST DIE.**",)
            await ctx.send(embed=a)
            await asyncio.sleep(.5)
            if role in member.roles:
                b = discord.Embed(description="I can not kill you, it's as if... You are already dead.")
                await ctx.send(embed=b)
            else:    
                c = discord.Embed(description=f"{ctx.author.mention} died due to unforseen circumstances. Don't worry, I didn't kill him.")
                await ctx.send(embed=c)
                await discord.Member.add_roles(member, role)
        else:    
            if member == ctx.author:
                if role in member.roles:
                    d = discord.Embed(description=f"{ctx.author.mention} tried to kill himself, but he is already dead.")
                    await ctx.send(embed=d)
                else:
                    e = discord.Embed(description=f"{ctx.author.mention} tried to kill themself, but it didn't seem to work.")
                    await ctx.send(embed=e)
            else:
                if role in member.roles:
                    f = discord.Embed(description=f"{ctx.author.mention} tried killing someone that is already is dead. How sad.")
                    await ctx.send(embed=f)
                else: 
                    g = discord.Embed(description=f'{member.mention} was killed by {ctx.author.mention}')
                    role = discord.utils.get(member.guild.roles, name='Dead')
                    await ctx.send(embed=g)
                    time.sleep(1)
                    await discord.Member.add_roles(member, role) 

#Suicide Command
    @commands.command(aliases=['commitdie', 'commitdeath'], brief="**For legal reasons this is a joke.** ||Just like you||")
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def suicide(self, ctx):
        member = ctx.author
        role = discord.utils.get(member.guild.roles, name='Dead')
        await ctx.message.delete()
        if role in member.roles:
            a = discord.Embed(description=f'{ctx.author.mention} tried killing themselves even though they are dead. How is that even possible? \n||(If you are having the thoughts of commiting suicide, please call +1 (800) 273-8255 or go to https://suicidepreventionlifeline.org. Otherwise, please ask a friend or a loved one for help.)||')
            ye = await ctx.send(embed=a)
            await asyncio.sleep(30)
            b = discord.Embed(description=f"{ctx.author.mention} tried killing themselves even though they are dead. How is that even possible?")
            await ye.edit(embed=b)
        else: 
            c = discord.Embed(description=f"{ctx.author.mention} commited death. \n||(If you are having the thoughts of commiting suicide, please call +1 (800) 273-8255 or go to https://suicidepreventionlifeline.org. Otherwise, please speak to a friend or a loved one for help.)||")
            ye2 = await ctx.send(embed=c)
            await asyncio.sleep(30)
            d = discord.Embed(description=f"{ctx.author.mention} commited death.")
            await ye2.edit(embed=d)
            time.sleep(0.5)
            await discord.Member.add_roles(member, role) 

#Alive Command
    @commands.command(aliases=['undie' 'life'], brief="Come back from the dead after you have been killed.")
    @commands.cooldown(1, 60, commands.BucketType.member)
    async def alive(self, ctx):
        member = ctx.author
        role = discord.utils.get(member.guild.roles, name='Dead')
        await ctx.message.delete()
        if role in member.roles:
            a = discord.Embed(description=f"{ctx.author.mention} came back from the dead.")
            await ctx.send(embed=a)
        else: 
            b = discord.Embed(description=f"{ctx.author.mention} tried to come back from the dead, but they are already alive.")
            await ctx.send(embed=b)
        await asyncio.sleep(0.5)
        await discord.Member.remove_roles(member, role)
       
#Revive Command
    @commands.command(brief="Bring people back to life.")
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def revive(self, ctx, member: discord.Member):
        await ctx.message.delete()
        role = discord.utils.get(member.guild.roles, name='Dead')
        if member == ctx.author:
            if role in member.roles:
                a = discord.Embed(description='Hmm, It seems that someone from the dead has spoken, I wonder who that is')
                await ctx.send(embed=a)
            else:
                b = discord.Embed(description='You are alive, why do you need to revive yourself?')
                await ctx.send(embed=b)
        else:
            role = discord.utils.get(member.guild.roles, name='Dead')
            c = discord.Embed(description=f"{ctx.author.mention} revived {member.mention}")
            await ctx.send(embed=c)
            time.sleep(0.5)
            await discord.Member.remove_roles(member, role)

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
        role = discord.utils.get(member.guild.roles, name='Server Owner')
        memberrr = ctx.author
        if member == self.avibot.user:
            a = discord.Embed(description="I don't have any skin, so you can not skin me.")
            await ctx.send(embed=a)
        if member.id == 672122220566413312:
            b = discord.Embed(description="You can not skin her!")
            await ctx.send(embed=b)
        else:
            if member == ctx.author:
                c = discord.Embed(description="You can't skin yourself")
                await ctx.send(embed=c)
            else:
                if role in member.roles:
                    d = discord.Embed(description=f"Stop that **{memberrr.display_name},** you can't skin him.")
                    await ctx.send(embed=d)
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

def setup(avibot):
    avibot.add_cog(Fun(avibot))