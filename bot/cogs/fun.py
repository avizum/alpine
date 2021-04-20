import discord
import random
import time
import asyncio
import akinator
from discord.ext import commands
from akinator.async_aki import Akinator
from utils.context import AvimetryContext


class Fun(commands.Cog):
    """
    Fun commands for you and your friends (if you have any) to use.
    """
    def __init__(self, avi):
        self.avi = avi
        self._cd = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.user)

    async def do_mock(self, string: str):
        return "".join(random.choice([mock.upper, mock.lower])() for mock in string)

# Magic 8 Ball
    @commands.command(
        aliases=["8ball", "8b"],
        brief="Ask the 8ball something",
    )
    @commands.cooldown(5, 15, commands.BucketType.member)
    async def eightball(self, ctx: AvimetryContext, *, question):
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
        if ctx.author.id in self.avi.owner_ids and question.lower().endswith(
            "\u200b"
        ):
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
    async def random(self, ctx: AvimetryContext, amount: int = 100):
        x = random.randint(1, amount)
        e = discord.Embed()
        e.add_field(name="Random Number", value=f"The number is {x}")
        await ctx.send(embed=e)

# Kill Command
    @commands.command(
        aliases=["murder"], brief="Kill some people. Make sure you don't get caught!"
    )
    @commands.cooldown(2, 30, commands.BucketType.member)
    async def kill(self, ctx: AvimetryContext, member: discord.Member):
        await ctx.message.delete()
        if member == self.avi.user or member.bot:
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

# Say Command
    @commands.command(
        brief="You can make me say whatever you please!", usage="<message>"
    )
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def say(self, ctx: AvimetryContext, *, botsay):
        await ctx.send_raw(f"{botsay}")

# Delete Say Command
    @commands.command(
        brief="You can make me say whatever you please, but I delete your message so it looks like I sent it!",
        usage="<message>",
    )
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def dsay(self, ctx: AvimetryContext, *, dbotsay):
        await ctx.message.delete()
        await ctx.send_raw(f"{dbotsay}")

# Skin Command
    @commands.command(brief="Remove the skin off of people that you don't like.")
    async def skin(self, ctx: AvimetryContext, member: discord.Member):
        await ctx.message.delete()
        if member == ctx.author:
            c = discord.Embed(description="You can't skin yourself, stupid")
            await ctx.send(embed=c)
        else:
            e = discord.Embed(description=f"{member.mention} was skinned.")
            await ctx.send(embed=e)

# Self destruct command
    @commands.command(aliases=["sd"], brief="Self destruct? Who put that button there?")
    async def selfdestruct(self, ctx: AvimetryContext):
        a = discord.Embed(
            description=f"{ctx.author.mention} self destructed due to overloaded fuel canisters"
        )
        await ctx.send(embed=a)

# Dropckick command
    @commands.command(brief="Drop kicks someone")
    async def dropkick(self, ctx: AvimetryContext, *, mention: discord.Member):
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
    async def facepalm(self, ctx: AvimetryContext):
        a = discord.Embed(description=f"{ctx.author.mention} hit their face.")
        await ctx.send(embed=a)

# Cookie Command
    @commands.command(
        brief="Get the cookie as fast as you can with out a countdown timer."
    )
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def cookie(self, ctx: AvimetryContext):
        cookie_embed = discord.Embed()
        cookie_embed.add_field(
            name="Get the cookie!",
            value="Who has the fastest reaction time? Get ready to grab the cookie!",
        )
        cd_cookie = await ctx.send(embed=cookie_embed)
        await asyncio.sleep(5)
        cookie_embed.set_field_at(
            0, name="Ready Up!", value="Get ready to get the cookie!"
        )
        await cd_cookie.edit(embed=cookie_embed)
        cntdown = (random.randint(1, 8))
        while cntdown > 0:
            await asyncio.sleep(1)
            cntdown -= 1
        await asyncio.sleep(1)
        cookie_embed.set_field_at(0, name="NOW!", value="Get the cookie now!")
        await cd_cookie.edit(embed=cookie_embed)
        await cd_cookie.add_reaction("\U0001F36A")
        start = time.perf_counter()

        def check(reaction, user):
            return (
                reaction.message.id == cd_cookie.id and str(reaction.emoji) in "\U0001F36A" and user != self.avi.user
            )

        try:
            reaction, user = await self.avi.wait_for(
                "reaction_add" or "reaction_remove", check=check, timeout=10
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

# Akinator Command
    @commands.command(
        name="akinator",
        aliases=["aki", "avinator"],
        brief="Play a game of akinator If you don't put anything, then it will default to `en` and `child=True`"
    )
    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def fun_akinator(self, ctx: AvimetryContext, mode="en", child=True):
        if ctx.me.permissions_in(ctx.channel).manage_messages is True:
            async def remove(message: discord.Message, emoji, user):
                await message.remove_reaction(emoji, user)

            async def clear(message: discord.Message):
                await message.clear_reactions()
        else:
            async def remove(message, emoji, user):
                return

            async def clear(message):
                return
        aki_dict = {
            "<:Yes:812133712967761951>": "yes",
            "<:No:812133712946528316>": "no",
            "<:IDontKnow:812133713046405230>": "idk",
            "<:Probably:812133712962519100>": "probably",
            "<:ProbablyNot:812133712665772113>": "probably not",
            "<:Back:815854941083664454>": "back",
            "<:Stop:815859174667452426>": "stop"
        }
        aki_react = []
        for emoji, answer in aki_dict.items():
            aki_react.append(emoji)
        aki_client = Akinator()
        akinator_embed = discord.Embed(
            title="Akinator",
            description=(
                "Current Settings:\n"
                f"Mode: `{mode}`\n"
                f"Child Mode: {child}\n"
                "[Here](https://gist.github.com/jbkn/8a5b9887d49a1d2740d0b6ad0176dbdb) are all the options for akinator"
            ),
        )
        async with ctx.channel.typing():
            initial_messsage = await ctx.send(embed=akinator_embed)
            q = await aki_client.start_game(mode, child)
        game_end_early = False
        for i in aki_react:
            await initial_messsage.add_reaction(i)
        await asyncio.sleep(5)
        akinator_embed.set_thumbnail(url="https://i.imgur.com/JMso9Kf.png")

        while aki_client.progression <= 80:
            print(aki_client.step)
            print(aki_client.progression)
            akinator_embed.description = f"{q}"
            await initial_messsage.edit(embed=akinator_embed)

            def check(reaction, user):
                return (
                    reaction.message.id == initial_messsage.id and
                    str(reaction.emoji) in aki_react and
                    user == ctx.author and
                    user != self.avi.user
                )

            done, pending = await asyncio.wait([
                self.avi.wait_for("reaction_remove", check=check, timeout=20),
                self.avi.wait_for("reaction_add", check=check, timeout=20)
            ], return_when=asyncio.FIRST_COMPLETED)

            try:
                reaction, user = done.pop().result()

            except asyncio.TimeoutError:
                await clear(initial_messsage)
                akinator_embed.description = (
                    "Akinator session closed because you took too long to answer."
                )
                akinator_embed.set_thumbnail(url=discord.Embed.Empty)
                await initial_messsage.edit(embed=akinator_embed)
                game_end_early = True
                return
            else:
                ans = aki_dict[str(reaction.emoji)]
                if ans == "stop":
                    game_end_early = True
                    akinator_embed.description = "Akinator session stopped."
                    akinator_embed.set_thumbnail(url=discord.Embed.Empty)
                    await initial_messsage.edit(embed=akinator_embed)
                    await clear(initial_messsage)
                    break
                elif ans == "back":
                    try:
                        q = await aki_client.back()
                    except akinator.CantGoBackAnyFurther:
                        pass
                else:
                    answer = ans

            finally:
                for future in done:
                    future.exception()
                for future in pending:
                    future.cancel()

            await remove(message=initial_messsage, emoji=reaction.emoji, user=user)
            q = await aki_client.answer(answer)
        try:
            await initial_messsage.clear_reactions()
        except discord.Forbidden:
            await initial_messsage.delete()
            initial_messsage = await ctx.send("Processing...")
        if game_end_early is True:
            return
        await aki_client.win()

        akinator_embed.description = (
            f"I think it is {aki_client.first_guess['name']} ({aki_client.first_guess['description']})! Was I correct?"
        )
        akinator_embed.set_thumbnail(
            url=discord.Embed.Empty
        )
        akinator_embed.set_image(
            url=f"{aki_client.first_guess['absolute_picture_path']}"
        )
        await initial_messsage.edit(embed=akinator_embed)
        reactions = ["<:greentick:777096731438874634>", "<:redtick:777096756865269760>"]
        for reaction in reactions:
            await initial_messsage.add_reaction(reaction)

        def yes_no_check(reaction, user):
            return (
                reaction.message.id == initial_messsage.id and
                str(reaction.emoji) in ["<:greentick:777096731438874634>", "<:redtick:777096756865269760>"] and
                user != self.avi.user and
                user == ctx.author
            )
        try:
            reaction, user = await self.avi.wait_for(
                "reaction_add", check=yes_no_check, timeout=60
            )
        except asyncio.TimeoutError:
            await clear(initial_messsage)
        else:
            await clear(initial_messsage)
            if str(reaction.emoji) == "<:greentick:777096731438874634>":
                akinator_embed.description = (
                    f"{akinator_embed.description}\n\n------\n\nYay!"
                )
                await initial_messsage.edit(embed=akinator_embed)
            if str(reaction.emoji) == "<:redtick:777096756865269760>":
                akinator_embed.description = (
                    f"{akinator_embed.description}\n\n------\n\nAww, maybe next time."
                )
                await initial_messsage.edit(embed=akinator_embed)

# Ship command
    @commands.command()
    async def ship(self, ctx: AvimetryContext, person1: discord.Member, person2: discord.Member):
        if person1.id == 750135653638865017 or person2.id == 750135653638865017:
            return await ctx.send(f"{person1.mention} and {person2.mention} are 0% compatible with each other")
        elif person1 == person2:
            return await ctx.send("Thats not how that works")
        percent = random.randint(0, 100)
        await ctx.send(f"{person1.mention} and {person2.mention} are {percent}% compatible with each other")

# PP size command
    @commands.command()
    async def ppsize(self, ctx: AvimetryContext, member: discord.Member = None):
        pp_embed = discord.Embed(
            title=f"{member.name}'s pp size",
            description=f"8{''.join('=' for i in range(random.randint(0, 12)))}D"
        )
        await ctx.send(embed=pp_embed)

# 10 second command
    @commands.command(
        name="10s",
        brief="Test your reaction time!",
        disabled=True
    )
    async def _10s(self, ctx: AvimetryContext):
        embed_10s = discord.Embed(
            title="10 seconds",
            description="Click the emoji in 10 seconds"
        )
        react_message = await ctx.send(embed=embed_10s)
        await react_message.add_reaction("\U0001F36A")
        start_time = time.perf_counter()

        def check_10s(reaction, user):
            return (
                reaction.message.id == react_message.id and str(reaction.emoji) in "\U0001F36A" and user == ctx.author
            )

        try:
            reaction, user = await self.avi.wait_for(
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
    async def mock(self, ctx: AvimetryContext, *, text):
        send = await self.do_mock(text)
        await ctx.send(send)

# Reddit Command
    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def reddit(self, ctx: AvimetryContext, subreddit):
        async with self.avi.session.get(f"https://www.reddit.com/r/{subreddit}.json") as content:
            stuff = await content.json()
        get_data = stuff["data"]["children"]
        if not get_data:
            return await ctx.send("No posts found in this subreddit.")
        data = random.choice(get_data)["data"]
        desc = data["selftext"] if data["selftext"] is not None else ""
        if len(desc) > 2048:
            desc = f'{data["selftext"][:2045]}...'
        embed = discord.Embed(
            title=data["title"],
            url=f"https://reddit.com{data['permalink']}",
            description=desc
        )
        url = data["url"]
        embed.set_image(url=url)
        embed.add_field(
            name="Post Info:",
            value=(
                f"<:upvote:818730949662867456> {data['ups']} "
                f"<:downvote:818730935829659665> {data['downs']}\n"
                f"Upvote ratio: {data['upvote_ratio']}\n"
            )
        )
        if data["over_18"]:
            new_embed = discord.Embed(
                title="NSFW Post",
                description="Are you sure you want to view it?\nIf you accept, It will be sent to your DMs."
            )
            res = await ctx.confirm(embed=new_embed)
            if res:
                return await ctx.author.send(embed=embed)
            if not res:
                return
        return await ctx.send(embed=embed)

# Meme command
    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def meme(self, ctx: AvimetryContext):
        reddit = self.avi.get_command("reddit")
        a = await reddit(ctx, subreddit="memes")
        print(a)

# Reaction time commnad
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def reaction(self, ctx: AvimetryContext):
        emoji = ["🍪", "🎉", "🧋", "🍒", "🍑"]
        random_emoji = random.choice(emoji)
        random.shuffle(emoji)
        embed = discord.Embed(
            title="Reaction time",
            description=f"After 1-30 seconds, a reaction ({random_emoji}) will be added to this message. "
        )
        first = await ctx.send(embed=embed)
        await asyncio.sleep(2.5)
        embed.description = f"Get ready to get the emoji ({random_emoji})!"
        await first.edit(embed=embed)
        await asyncio.sleep(random.randint(1, 30))
        embed.description = "GO!!"
        await first.edit(embed=embed)
        for emojis in emoji:
            await first.add_reaction(emojis)
        start = time.perf_counter()

        def check(reaction, user):
            return(
                reaction.message.id == first.id and str(reaction.emoji) == random_emoji and user != self.avi.user
            )

        try:
            reaction, user = await self.avi.wait_for("reaction_add", check=check, timeout=15)
        except asyncio.TimeoutError:
            print("timeout")
        else:

            if str(reaction.emoji) == random_emoji:
                end = time.perf_counter()
                gettime = (end - start) * 1000
                total_second = f"**{round(gettime)}ms**"
                if gettime > 1000:
                    gettime = gettime / 1000
                    total_second = f"**{gettime:.2f}s**"
                embed.description = f"{user.mention} got the {random_emoji} in {total_second}"
                await first.edit(embed=embed)

    @commands.command(name="guessthatlogo", aliases=["gtl"])
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_guess_that_logo(self, ctx):
        async with ctx.channel.typing():
            logo = await self.avi.dagpi.logo()
        embed = discord.Embed(
            title="Which logo is this?",
            description=f"{logo.clue}"
        )
        embed.set_image(url=logo.question)
        message = await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author

        wait = await self.avi.wait_for("message", check=check, timeout=60)
        if wait.content.lower() == logo.brand.lower():
            embed.title = "🎉 Good Job 🎉"
            embed.description = f"The answer was {logo.brand}"
            embed.set_image(url=logo.answer)
            return await message.edit(embed=embed)
        embed.title = f"{self.avi.emoji_dictionary['red_tick']} | Wrong"
        embed.description = f"Your answer was {wait.content}.\nThe correct answer is actually {logo.brand}"
        embed.set_image(url=logo.answer)
        await message.edit(embed=embed)

    @commands.command(name="roast")
    async def dag_roast(self, ctx, member: discord.Member):
        roast = await self.avi.dagpi.roast()
        await ctx.send(f"{member.mention}, {roast}")


def setup(avi):
    avi.add_cog(Fun(avi))
