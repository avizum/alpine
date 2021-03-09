import discord
from discord.ext import commands
import random
import time
import asyncio
import akinator
from akinator.async_aki import Akinator


class Fun(commands.Cog):
    """
    Fun commands for you and your friends to use.
    """
    def __init__(self, avimetry):
        self.avimetry = avimetry
        self._cd = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.user)

# Magic 8 Ball
    @commands.command(
        aliases=["8ball", "8b"],
        brief="Ask the 8ball something",
    )
    @commands.cooldown(5, 15, commands.BucketType.member)
    async def eightball(self, ctx, *, question):
        responses = [
            "As I see it, yes.", "Ask again later.",
            "Better not tell you now.", "Cannot predict now.",
            "Concentrate and ask again.", "Don’t count on it.",
            "It is certain.", "It is decidedly so.",
            "Most likely.", "My reply is no.",
            "My sources say no.", "Outlook not so good.",
            "Outlook good.", "Reply hazy, try again.",
            "Signs point to yes.", "Very doubtful.",
            "Without a doubt.", "Yes.",
            "Yes – definitely.", "You may rely on it.",
        ]
        if ctx.author.id in self.avimetry.owner_ids:
            if question.lower().endswith("\u200b"):
                responses = [
                    "It is certain.", "Without a doubt.",
                    "You may rely on it.", "Yes definitely.",
                    "It is decidedly so.", "As I see it, yes.",
                    "Most likely.", "Yes.",
                    "Outlook good.", "Signs point to yes.",
                ]
        ballembed = discord.Embed(title=":8ball: Magic 8 Ball")
        ballembed.add_field(name="Question:", value=f"{question}", inline=False)
        ballembed.add_field(
            name="Answer:", value=f"{random.choice(responses)}", inline=False
        )
        await ctx.send(embed=ballembed)

# Random Number
    @commands.command(brief="Pick a random number from 1 to 100", usage="[amount]")
    async def random(self, ctx, amount: int = 100):
        x = random.randint(1, amount)
        e = discord.Embed()
        e.add_field(name="Random Number", value=f"The number is {x}")
        await ctx.send(embed=e)

# Kill Command
    @commands.command(
        aliases=["murder"], brief="Kill some people. Make sure you don't get caught!"
    )
    @commands.cooldown(2, 30, commands.BucketType.member)
    async def kill(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if member == self.avimetry.user or member.bot:
            await ctx.send("You fool. Us bots can't die")

        else:
            if member == ctx.author:
                await ctx.send(
                    f"{ctx.author.mention} tried to kill themself, but your friend caught you and decided to bring "
                    "you to the hospital. On the way to the hospital, your friend crashed the car. They both died."
                )
            else:
                author = ctx.author.mention
                member = member.mention
                kill_response = [
                    f"{author} killed {member}.",
                    f"{author} murdered {member} with a machine gun.",
                    f"{author} accidentally shot themselves in the face while trying to load the gun",
                    f"{author} died while summoning a demon to kill {member}",
                    f"A demon killed {member} because {author} summoned a demon.",
                    f"{author} was caught by the police because he was mumbling his plans to to kill {member}",
                    f"{author} hired a hitman to kill {member}.",
                    f"{author} shot and killed {member} then reloaded the gun, only to shoot himself in the face.",
                    f"{author} chopped {member}'s head off with a guillotine",
                    f"{author} sniped {member} at the store.",
                    f"{author} tried poisoned {member} but {author} forgot to wear a mask so they fainted",
                    f"{author} died whilst fighting {member}.",
                    f"{member} was stoned to death by {author}.",
                    f"{member} was almost killed by {author} but {member} took the gun from him and shot {author}",
                ]
                await ctx.send(f"{random.choice(kill_response)}")

# Revive Command
    @commands.command(brief="Bring people back to life.")
    @commands.cooldown(5, 30, commands.BucketType.member)
    async def revive(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if member == ctx.author:
            await ctx.send("{ctx.author.mention} has come back from the dead")
        else:
            await ctx.send(f"{ctx.author.mention} revived {member.mention}")

# Say Command
    @commands.command(
        brief="You can make me say whatever you please!", usage="<message>"
    )
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def say(self, ctx, *, botsay):
        await ctx.send_raw(f"{botsay}")

# Delete Say Command
    @commands.command(
        brief="You can make me say whatever you please, but I delete your message so it looks like I sent it!",
        usage="<message>",
    )
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def dsay(self, ctx, *, dbotsay):
        await ctx.message.delete()
        await ctx.send_raw(f"{dbotsay}")

# Skin Command
    @commands.command(brief="Remove the skin off of people that you don't like.")
    async def skin(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if member == ctx.author:
            c = discord.Embed(description="You can't skin yourself, stupid")
            await ctx.send(embed=c)
        else:
            e = discord.Embed(description=f"{member.mention} was skinned.")
            await ctx.send(embed=e)

# Self destruct command
    @commands.command(aliases=["sd"], brief="Self destruct? Who put that button there?")
    async def selfdestruct(self, ctx):
        a = discord.Embed(
            description=f"{ctx.author.mention} self destructed due to overloaded fuel canisters"
        )
        await ctx.send(embed=a)

# Dropckick command
    @commands.command(brief="Drop kicks someone")
    async def dropkick(self, ctx, *, mention: discord.Member):
        if mention == ctx.author:
            a = discord.Embed(
                description=f"{ctx.author.mention} tried dropkicking themselves"
            )
            await ctx.send(embed=a)
        else:
            b = discord.Embed(
                description=f"{ctx.author.mention} dropkicked {mention.mention}"
            )
            await ctx.send(embed=b)

# Face Palm Command
    @commands.command(
        aliases=["fp", "facep", "fpalm"], brief="Hit yourself on the face!"
    )
    async def facepalm(self, ctx):
        a = discord.Embed(description=f"{ctx.author.mention} hit their face.")
        await ctx.send(embed=a)

# Cookie Command
    @commands.command(
        brief="Get the cookie as fast as you can with out a countdown timer."
    )
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def cookie(self, ctx):
        cookie_embed = discord.Embed()
        cookie_embed.add_field(
            name="Get the cookie!",
            value="Who has the fastest reaction time? Get ready to grab the cookie!",
        )
        cd_cookie = await ctx.send_raw(embed=cookie_embed)
        await asyncio.sleep(5)
        cookie_embed.set_field_at(
            0, name="Ready Up!", value="Get ready to get the cookie!"
        )
        await cd_cookie.edit(embed=cookie_embed)
        cntdown = (random.randint(1, 8))
        while cntdown > 0:
            await asyncio.sleep(1)
            cookie_embed.set_field_at(
                0, name="Get Ready", value=f"Get the cookie in {cntdown}"
            )
            await cd_cookie.edit(embed=cookie_embed)
            cntdown -= 1
        await asyncio.sleep(1)
        cookie_embed.set_field_at(0, name="NOW!", value="Get the cookie now!")
        await cd_cookie.edit(embed=cookie_embed)
        await cd_cookie.add_reaction("\U0001F36A")
        start = time.perf_counter()

        def check(reaction, user):
            return (
                reaction.message.id == cd_cookie.id and
                str(reaction.emoji) in "\U0001F36A" and
                user != self.avimetry.user
            )

        try:
            reaction, user = await self.avimetry.wait_for(
                "reaction_add", check=check, timeout=10
            )
        except asyncio.TimeoutError:
            cookie_embed.set_field_at(
                0, name="Game over!", value="Nobody got the cookie :("
            )
            await cd_cookie.edit(embed=cookie_embed)
            await cd_cookie.clear_reactions()
        else:
            if str(reaction.emoji) == "\U0001F36A":
                end = time.perf_counter()
                gettime = (end - start) * 1000
                total_second = f"**{round(gettime)}ms**"
                if gettime > 1000:
                    gettime = gettime / 1000
                    total_second = f"**{gettime:.2f}s**"
                cookie_embed.set_field_at(
                    0,
                    name="Good job!",
                    value=f"{user.mention} got the cookie in **{total_second}**",
                )
                return await cd_cookie.edit(embed=cookie_embed)

# Suicide Command (Joke)
    @commands.command(hidden=True)
    async def suicide(self, ctx):
        pre = await self.avimetry.get_prefix(ctx.message)
        embed = discord.Embed(
            title="Invalid Command",
            description="I wasn't about to find a command called \"suicide\". Did you mean...\n`don't\ndo\nit`",
            color=discord.Color.red(),
        )
        embed.set_footer(
            text=f"Not what you meant? Use {pre}help to see the whole list of commands."
        )
        await ctx.send(embed=embed)

# Akinator Command
    @commands.command(
        name="akinator",
        aliases=["aki", "avinator"],
        brief="Play a game of akinator If you don't put anything, then it will default to `en` and `child=True`"
    )
    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def fun_akinator(self, ctx, mode="en", child=True):
        aki_client = Akinator()
        akinator_embed = discord.Embed(
            title="Akinator",
            description=(
                "Starting akinator session.\n\
                React with the emojis below to answer.\n\
                <:Yes:812133712967761951>: Yes\n\
                <:No:812133712946528316>: No\n\
                <:IDontKnow:812133713046405230>: I don't know\n\
                <:Probably:812133712962519100>: Probably\n\
                <:ProbablyNot:812133712665772113>: Probably Not\n\
                <:Back:815854941083664454>: Go back\n\
                If you need more help, click [here](https://gist.github.com/jbkn/8a5b9887d49a1d2740d0b6ad0176dbdb)"
            ),
        )
        async with ctx.channel.typing():
            initial_messsage = await ctx.send(embed=akinator_embed)
            q = await aki_client.start_game(mode, child)
        game_end_early = False
        akinator_reactions = [
            "<:Yes:812133712967761951>",
            "<:No:812133712946528316>",
            "<:IDontKnow:812133713046405230>",
            "<:Probably:812133712962519100>",
            "<:ProbablyNot:812133712665772113>",
            "<:Back:815854941083664454>",
            "<:Stop:815859174667452426>"
        ]
        for i in akinator_reactions:
            await initial_messsage.add_reaction(i)
        await asyncio.sleep(5)
        akinator_embed.set_thumbnail(url="https://i.imgur.com/c1KE1Ky.png")

        while aki_client.progression <= 80:
            akinator_embed.description = q
            await initial_messsage.edit(embed=akinator_embed)

            def check(reaction, user):
                return (
                    reaction.message.id == initial_messsage.id and
                    str(reaction.emoji) in akinator_reactions and
                    user == ctx.author and
                    user != self.avimetry.user
                )

            try:
                reaction, user = await self.avimetry.wait_for(
                    "reaction_add", check=check, timeout=20
                )
            except asyncio.TimeoutError:
                await initial_messsage.clear_reactions()
                akinator_embed.description = (
                    "Akinator session closed because you took too long to answer."
                )
                akinator_embed.set_thumbnail(url=discord.Embed.Empty)
                await initial_messsage.edit(embed=akinator_embed)
                game_end_early = True
                break
            else:
                await initial_messsage.remove_reaction(reaction.emoji, user)
                if str(reaction.emoji) == "<:Yes:812133712967761951>":
                    ans = "yes"
                elif str(reaction.emoji) == "<:No:812133712946528316>":
                    ans = "no"
                elif str(reaction.emoji) == "<:IDontKnow:812133713046405230>":
                    ans = "idk"
                elif str(reaction.emoji) == "<:Probably:812133712962519100>":
                    ans = "probably"
                elif str(reaction.emoji) == "<:ProbablyNot:812133712665772113>":
                    ans = "probably not"
                elif str(reaction.emoji) == "<:Back:815854941083664454>":
                    ans = "back"
                elif str(reaction.emoji) == "<:Stop:815859174667452426>":
                    game_end_early = True
                    akinator_embed.description = "Akinator session stopped."
                    akinator_embed.set_thumbnail(url=discord.Embed.Empty)
                    await initial_messsage.edit(embed=akinator_embed)
                    await initial_messsage.clear_reactions()
                    break

            if ans == "back":
                try:
                    q = await aki_client.back()
                except akinator.CantGoBackAnyFurther:
                    pass
            else:
                q = await aki_client.answer(ans)
        await initial_messsage.clear_reactions()
        if game_end_early is True:
            return
        await aki_client.win()

        akinator_embed.description = (
            f"I think it is {aki_client.first_guess['name']} ({aki_client.first_guess['description']})! Was I correct?"
        )
        akinator_embed.set_thumbnail(
            url=f"{aki_client.first_guess['absolute_picture_path']}"
        )
        await initial_messsage.edit(embed=akinator_embed)
        reactions = ["<:yesTick:777096731438874634>", "<:noTick:777096756865269760>"]
        for reaction in reactions:
            await initial_messsage.add_reaction(reaction)

        def yes_no_check(reaction, user):
            return (
                reaction.message.id == initial_messsage.id and
                str(reaction.emoji) in ["<:yesTick:777096731438874634>", "<:noTick:777096756865269760>"] and
                user != self.avimetry.user and
                user == ctx.author
            )
        try:
            reaction, user = await self.avimetry.wait_for(
                "reaction_add", check=yes_no_check, timeout=60
            )
        except asyncio.TimeoutError:
            await initial_messsage.clear_reactions()
        else:
            await initial_messsage.clear_reactions()
            if str(reaction.emoji) == "<:yesTick:777096731438874634>":
                akinator_embed.description = (
                    f"{akinator_embed.description}\n\n------\n\nYay!"
                )
                await initial_messsage.edit(embed=akinator_embed)
            if str(reaction.emoji) == "<:noTick:777096756865269760>":
                akinator_embed.description = (
                    f"{akinator_embed.description}\n\n------\n\nAww, maybe next time."
                )
                await initial_messsage.edit(embed=akinator_embed)

    @commands.command()
    async def ship(self, ctx, person1: discord.Member, person2: discord.Member):
        if person1.id == 750135653638865017 or person2.id == 750135653638865017:
            return await ctx.send("You can not ship him. He is forever alone.")
        elif person1 == person2:
            return await ctx.send(f"{person1} is 100% compatible with him/herself")
        percent = random.randint(0, 100)
        await ctx.send(f"{person1} + {person2} = {percent}%")

# 10 second command
    @commands.command(
        name="10s",
        brief="Test your reaction time!",
        disabled=True
    )
    async def _10s(self, ctx):
        embed_10s = discord.Embed(
            title="10 seconds",
            description="Click the emoji in 10 seconds"
            )
        react_message = await ctx.send(embed=embed_10s)
        await react_message.add_reaction("\U0001F36A")
        start_time = time.perf_counter()

        def check_10s(reaction, user):
            return (
                reaction.message.id == react_message.id and
                str(reaction.emoji) in "\U0001F36A" and
                user == ctx.author
            )

        try:
            reaction, user = await self.avimetry.wait_for(
                "reaction_add", check=check_10s, timeout=20
            )
        except asyncio.TimeoutError:
            pass
        else:
            if str(reaction.emoji) == "\U0001F36A":
                end_time = time.perf_counter()
                gettime = (end_time - start_time)
                final_time = gettime
                if final_time < 5.0:
                    embed_10s.description = "You are supposed to wait 10 seconds to get the cookie"
                    return await react_message.edit(embed=embed_10s)
                embed_10s.description = (
                    f"You got the cookie in {final_time:.2f} seconds\n"
                )
                await react_message.edit(embed=embed_10s)

# Mock Command
    @commands.command()
    async def mock(self, ctx, *, text):
        await ctx.send("".join(random.choice([mock.upper, mock.lower])() for mock in text))

# Reddit Command
    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def reddit(self, ctx, subreddit):
        async with self.avimetry.session.get(f"https://www.reddit.com/r/{subreddit}.json") as content:
            stuff = await content.json()
        get_data = stuff["data"]["children"]
        data = random.choice(get_data)["data"]
        embed = discord.Embed(
            title=data["title"],
            url=f"https://reddit.com{data['permalink']}",
            description=(
                f"<:upvote:818730949662867456> {data['ups']} "
                f"<:downvote:818730935829659665> {data['downs']}\n"
                f"Upvote ratio: {data['upvote_ratio']}\n"
                f"[Image link]({data['url']})"
            ))
        if "mp4" in data["url"]:
            embed.description = "The filetype of the media is unsupported by Discord."
        else:
            embed.set_image(url=data["url"])
        await ctx.send(embed=embed)

# Meme command
    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def meme(self, ctx):
        reddit = self.avimetry.get_command("reddit")
        await reddit(ctx, subreddit="memes")


def setup(avimetry):
    avimetry.add_cog(Fun(avimetry))
