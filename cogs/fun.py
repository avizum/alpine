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
    @eightball.error
    async def purgeErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            _8busage=discord.Embed()
            _8busage.add_field(name="Usage: a.8b", value="a.8b [question]")
            await ctx.send(embed=_8busage)

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
            await ctx.send('You fool. I can not die. Now **YOU MUST DIE.**')
            time.sleep(.5)
            if role in member.roles:
                await ctx.send("I can not kill you, it's as if... You are already dead.")
            else:    
                await ctx.send(f"{ctx.author.mention} was killed by me. Don't you ever try to kill me again.")
                await discord.Member.add_roles(member, role)
        else:    
            if member == ctx.author:
                await ctx.send(f"{ctx.author.mention} tried to kill themself, but it didn't seem to work.")
            else:
                if role in member.roles:
                    await ctx.send(f"{ctx.author.mention} tried killing someone that is already is dead. How sad.")
                else: 
                    role = discord.utils.get(member.guild.roles, name='Dead')
                    await ctx.send(f'{member.mention} was killed by {ctx.author.mention}')
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
            ye = await ctx.send(f'{ctx.author.mention} tried killing themselves even though they are dead. How is that even possible? \n(If you are having the thoughts of commiting suicide, please call +1 (800) 273-8255 or go to https://suicidepreventionlifeline.org. Otherwise, please ask a friend or a loved one for help.)')
            await asyncio.sleep(30)
            await ye.edit(content=f"{ctx.author.mention} tried killing themselves even though they are dead. How is that even possible?")
        else: 
            ye2 = await ctx.send(content=f"{ctx.author.mention} commited death \n(If you are having the thoughts of commiting suicide, please call +1 (800) 273-8255 or go to https://suicidepreventionlifeline.org. Otherwise, please speak to a friend or a loved one for help.)")
            await asyncio.sleep(30)
            await ye2.edit(f"{ctx.author.mention} commited death.")
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
            await ctx.send(f"{ctx.author.mention} came back from the dead.")
        else: 
            await ctx.send(f"{ctx.author.mention} tried to come back from the dead, but they are already alive.")
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
                await ctx.send('Hmm, It seems that someone from the dead has spoken, I wonder who that is')
            else:
                await ctx.sed('You are alive, why do you need to revive yourself?')
        else:
            role = discord.utils.get(member.guild.roles, name='Dead')
            await ctx.send(f"{ctx.author.mention} revived {member.mention}")
            time.sleep(0.5)
            await discord.Member.remove_roles(member, role)


#Say Command
    @commands.command(brief="You can make me say whatever you please!")
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def say(self, ctx, *, botsay):
        await ctx.send(f'{botsay}')

    @say.error
    async def sayErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            rc=discord.Embed(title="Command: revive")
            rc.add_field(name="Description:", value="Revives a person", inline=False)
            rc.add_field(name="Example:", value=f"`{pre}revive [user]`", inline=False)
            rc.add_field(name="Cooldown:", value="Thirty second cooldown", inline=False)
            await ctx.send(embed=rc)

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
            await ctx.send("I don't have any skin, so you can not skin me.")
        if member == 672122220566413312:
            await ctx.send("You can not skin her!")
        else:
            if member == ctx.author:
                await ctx.send("You can't skin yourself")
            else:
                if role in member.roles:
                    await ctx.send(f"Stop that **{memberrr.display_name},** you can't skin him.")
                else:
                    await ctx.send(f'{member.mention} was skinned.')
    @skin.error
    async def skinErr(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            sc=discord.Embed(title="Command: skin")
            sc.add_field(name="Description:", value="Skins a person", inline=False)
            sc.add_field(name="Example:", value=f"{pre}skin [user]", inline=False)
            await ctx.send(embed=sc)

    @commands.command(aliases=['sd'], brief="Self destruct? Who put that button there?")
    async def selfdestruct(self, ctx):
        await ctx.send(f"{ctx.author.mention} self destructed due to overloaded fuel canisters")

    @commands.command(brief="Drop kicks someone")
    async def dropkick(self, ctx, *, mention:discord.Member):
        if mention == ctx.author:
            await ctx.send(f"{ctx.author.mention} tried dropkicking themselves")
        else:
            await ctx.send(f'{ctx.author.mention} dropkicked {mention.mention}')
def setup(avibot):
    avibot.add_cog(Fun(avibot))