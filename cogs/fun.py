"""
Fun commands for users
Copyright (C) 2021 avizum

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
import random
import time
import asyncio
import akinator
import typing
from discord.ext import commands
from akinator.async_aki import Akinator
from utils import AvimetryBot, AvimetryContext


class Fun(commands.Cog):
    """
    Fun commands for you and friends.
    """
    def __init__(self, avi):
        self.avi: AvimetryBot = avi
        self._cd = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.user)

    async def do_mock(self, string: str):
        return "".join(random.choice([mock.upper, mock.lower])() for mock in string)

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

    @commands.command(brief="Pick a random number from 1 to 100", usage="[amount]")
    async def random(self, ctx: AvimetryContext, amount: int = 100):
        x = random.randint(1, amount)
        e = discord.Embed()
        e.add_field(name="Random Number", value=f"The number is {x}")
        await ctx.send(embed=e)

    @commands.command(
        aliases=["murder"], brief="Kill some people. Make sure you don't get caught!")
    @commands.cooldown(2, 30, commands.BucketType.member)
    async def kill(self, ctx: AvimetryContext, member: discord.Member):
        if member == self.avi.user or member.bot:
            await ctx.send("Nope.")
        else:
            if member == ctx.author:
                await ctx.send("You tried to shoot yourself in the head, but you couldn't because I won't let you :)")
            else:
                author = ctx.author.mention
                member = member.mention
                kill_response = [
                    f"{author} killed {member}.",
                    f"{author} murdered {member} with a machine gun.",
                    f"{author} accidentally shot themselves in the face while trying to load the gun.",
                    f"{author} died while summoning a demon to kill {member}",
                    f"{member} summoned a demon to kill {author}.",
                    f"{author} was caught by the police because he posted his plans to kill {member}",
                    f"{author} hired a hitman to kill {member}.",
                    f"{author} shot {member}. While reloading the gun, {author} shot themselves on the head.",
                    f"{author} kidnapped {member} and chopped their head off with a guillotine",
                    f"{author} sniped {member} at the store.",
                    f"{author} tried to poison {member} but {author} put the poison in their drink.",
                    f"{author} died whilst fighting {member}.",
                    f"{member} was stoned to death by {author}.",
                    f"{member} was almost killed by {author} but {member} took the gun and shot {author}",
                ]
                await ctx.send(f"{random.choice(kill_response)}")

    @commands.command(brief="Makes me say a message")
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def say(self, ctx: AvimetryContext, *, message):
        await ctx.send_raw(message)

    @commands.command(brief="Makes me say a message but I delete your message")
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def dsay(self, ctx: AvimetryContext, *, message):
        await ctx.message.delete()
        await ctx.send_raw(message)

    @commands.command(
        brief="Copies someone so it looks like a person actually sent the message."
    )
    @commands.bot_has_permissions(manage_webhooks=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def copy(self, ctx: AvimetryContext, member: typing.Union[discord.User, discord.Member], *, text):
        if member == self.avi.user:
            say = self.avi.get_command("say")
            return await say(ctx, message=text)
        webhooks = await ctx.channel.webhooks()
        avimetry_webhook = discord.utils.get(webhooks, name="Avimetry")
        if not avimetry_webhook:
            avimetry_webhook = await ctx.channel.create_webhook(
                name="Avimetry", reason="For Avimetry copy command.",
                avatar=await self.avi.user.avatar_url.read())
        await avimetry_webhook.send(
            text, username=member.display_name,
            avatar_url=member.avatar_url_as(format="png"),
            allowed_mentions=discord.AllowedMentions.none())

    @commands.command(
        aliases=["fp", "facep", "fpalm"]
    )
    async def facepalm(self, ctx: AvimetryContext, member: discord.Member = None):
        if member is None:
            return await ctx.send(f"{ctx.author.mention} hit their head")
        return await ctx.send(f"{ctx.author.mention} hit their head because {member.mention} was being stupid.")

    @commands.command(brief="Remove the skin off of people that you don't like.")
    async def skin(self, ctx: AvimetryContext, member: discord.Member):
        await ctx.message.delete()
        if member == ctx.author:
            c = discord.Embed(description="You can't skin yourself, stupid")
            await ctx.send(embed=c)
        else:
            e = discord.Embed(description=f"{member.mention} was skinned.")
            await ctx.send(embed=e)

    @commands.command(aliases=["sd"], brief="Self destruct? Who put that there?")
    async def selfdestruct(self, ctx: AvimetryContext):
        a = discord.Embed(
            description=f"{ctx.author.mention} self destructed due to overloaded fuel canisters")
        await ctx.send(embed=a)

    @commands.command(brief="Dropkick someone")
    async def dropkick(self, ctx: AvimetryContext, *, mention: discord.Member):
        if mention == ctx.author:
            embed = discord.Embed(description=f"{ctx.author.mention} tried dropkicking themselves.")
        else:
            embed = discord.Embed(
                description=f"{ctx.author.mention} dropkicked {mention.mention}, killing them.")
        await ctx.send(embed=embed)

    @commands.command(brief="Try to get the cookie as fast as you can!")
    @commands.cooldown(1, 30, commands.BucketType.member)
    async def cookie(self, ctx: AvimetryContext):
        cookie_embed = discord.Embed()
        cookie_embed.add_field(
            name="Get the cookie!",
            value="Who has the fastest reaction time? Get ready to grab the cookie!")
        cd_cookie = await ctx.send(embed=cookie_embed)
        await asyncio.sleep(5)
        cookie_embed.set_field_at(
            0, name="Ready Up!", value="Get ready to get the cookie!")
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

    async def remove(self, message: discord.Message, emoji, user, perm: bool):
        if not perm:
            return
        await message.remove_reaction(emoji, user)

    async def clear(self, message: discord.Message, perm: bool):
        if not perm:
            return
        await message.clear_reactions()

    @commands.command(
        name="akinator",
        aliases=["aki", "avinator"],
        brief="Play a game of akinator If you don't put anything, then it will default to `en` and `child=True`")
    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def fun_akinator(self, ctx: AvimetryContext, mode="en", child=True):
        bot_perm = ctx.me.permissions_in(ctx.channel)
        perms = True if bot_perm.manage_messages is True else False
        aki_dict = {
            "<:Yes:812133712967761951>": "yes",
            "<:No:812133712946528316>": "no",
            "<:IDontKnow:812133713046405230>": "idk",
            "<:Probably:812133712962519100>": "probably",
            "<:ProbablyNot:812133712665772113>": "probably not",
            "<:Back:815854941083664454>": "back",
            "<:Stop:815859174667452426>": "stop"
        }
        aki_react = [emoji for emoji in aki_dict]
        aki_client = Akinator()
        akinator_embed = discord.Embed(
            title="Akinator",
            description=(
                "Current Settings:\n"
                f"Mode: `{mode}`\n"
                f"Child Mode: {child}\n"
                "[Here](https://gist.github.com/jbkn/8a5b9887d49a1d2740d0b6ad0176dbdb) are all the options for akinator"
            )
        )
        async with ctx.channel.typing():
            initial_messsage = await ctx.send(embed=akinator_embed)
            game = await aki_client.start_game(mode, child)
        for i in aki_react:
            await initial_messsage.add_reaction(i)
        await asyncio.sleep(5)
        akinator_embed.set_thumbnail(url="https://i.imgur.com/JMso9Kf.png")

        while aki_client.progression <= 80:
            akinator_embed.description = game
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
                await self.clear(initial_messsage, perms)
                akinator_embed.description = (
                    "Akinator session closed because you took too long to answer."
                )
                akinator_embed.set_thumbnail(url=discord.Embed.Empty)
                await initial_messsage.edit(embed=akinator_embed)
                break
            else:
                ans = aki_dict[str(reaction.emoji)]
                if ans == "stop":
                    akinator_embed.description = "Akinator session stopped."
                    akinator_embed.set_thumbnail(url=discord.Embed.Empty)
                    await initial_messsage.edit(embed=akinator_embed)
                    await self.clear(initial_messsage, perms)
                    break
                elif ans == "back":
                    try:
                        game = await aki_client.back()
                    except akinator.CantGoBackAnyFurther:
                        pass
                else:
                    answer = ans

            finally:
                for future in done:
                    future.exception()
                for future in pending:
                    future.cancel()

            await self.remove(initial_messsage, reaction.emoji, user, perms)
            game = await aki_client.answer(answer)
        try:
            await initial_messsage.clear_reactions()
        except discord.Forbidden:
            await initial_messsage.delete()
            initial_messsage = await ctx.send("Processing...")
        await aki_client.win()

        akinator_embed.description = (
            f"I think it is {aki_client.first_guess['name']} ({aki_client.first_guess['description']})! Was I correct?"
        )
        akinator_embed.set_thumbnail(url=discord.Embed.Empty)
        akinator_embed.set_image(url=f"{aki_client.first_guess['absolute_picture_path']}")
        await initial_messsage.edit(embed=akinator_embed)
        reactions = ["<:greentick:777096731438874634>", "<:redtick:777096756865269760>"]
        for reaction in reactions:
            await initial_messsage.add_reaction(reaction)

        def yes_no_check(reaction, user):
            return (
                reaction.message.id == initial_messsage.id and
                (reaction.emoji) in ["<:greentick:777096731438874634>", "<:redtick:777096756865269760>"] and
                user != self.avi.user and
                user == ctx.author
            )
        try:
            reaction, user = await self.avi.wait_for(
                "reaction_add", check=yes_no_check, timeout=60
            )
        except asyncio.TimeoutError:
            await self.clear(initial_messsage, perms)
        else:
            await self.clear(initial_messsage, perms)
            if str(reaction.emoji) == "<:greentick:777096731438874634>":
                akinator_embed.description = (
                    f"{akinator_embed.description}\n\n------\n\nYay!"
                )
            if str(reaction.emoji) == "<:redtick:777096756865269760>":
                akinator_embed.description = (
                    f"{akinator_embed.description}\n\n------\n\nAww, maybe next time."
                )
            await initial_messsage.edit(embed=akinator_embed)

    @commands.command(
        brief="Check if a person is compatible with another person."
    )
    async def ship(self, ctx: AvimetryContext, person1: discord.Member, person2: discord.Member):
        if person1.id == 750135653638865017 or person2.id == 750135653638865017:
            return await ctx.send(f"{person1.mention} and {person2.mention} are 0% compatible with each other")
        elif person1 == person2:
            return await ctx.send("Thats not how that works")
        percent = random.randint(0, 100)
        await ctx.send(f"{person1.mention} and {person2.mention} are {percent}% compatible with each other")

    @commands.command(
        brief="Get the PP size of someone"
    )
    async def ppsize(self, ctx: AvimetryContext, member: discord.Member = None):
        pp_embed = discord.Embed(
            title=f"{member.name}'s pp size",
            description=f"8{''.join('=' for i in range(random.randint(0, 12)))}D"
        )
        await ctx.send(embed=pp_embed)

    @commands.command(
        name="10s",
        brief="Test your reaction time!",
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
                    embed_10s.description = "Wait 10 seconds to get the cookie."
                    return await react_message.edit(embed=embed_10s)
                embed_10s.description = (
                    f"You got the cookie in {final_time:.2f} seconds with {final_time-10} reaction time\n"
                )
                await react_message.edit(embed=embed_10s)

    @commands.command(
        brief="Gets a random post from a subreddit"
    )
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def reddit(self, ctx: AvimetryContext, subreddit):
        async with self.avi.session.get(f"https://www.reddit.com/r/{subreddit}.json") as content:
            stuff = await content.json()
        get_data = stuff["data"]["children"]
        if not get_data:
            return await ctx.send("No posts found in this subreddit.")
        try:
            data = random.choice(get_data)["data"]
        except Exception:
            return await ctx.send("No posts found.")
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

    @commands.command(
        brief="Gets a meme from r/memes | r/meme subreddits."
    )
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def meme(self, ctx: AvimetryContext):
        reddit = self.avi.get_command("reddit")
        subreddits = ["memes", "meme"]
        a = await reddit(ctx, subreddit=random.choice(subreddits))
        print(a)

    @commands.command(
        brief="See how fast you can react with the correct emoji."
    )
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

        def check(reaction, user):
            return(
                reaction.message.id == first.id and str(reaction.emoji) == random_emoji and user != self.avi.user)
        start = time.perf_counter()
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

    @commands.command(
        name="guessthatlogo",
        aliases=["gtl"],
        brief="Try to guess the name of a logo. (Powered by Dagpi)"
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_guess_that_logo(self, ctx: AvimetryContext):
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

        try:
            wait = await self.avi.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            embed.title = f"{self.avi.emoji_dictionary['red_tick']} | Time's Up!"
            embed.description = f"You took too long. The correct answer is {logo.brand}"
            try:
                embed.set_image(url=logo.answer)
            except discord.HTTPException:
                pass
            await message.edit(embed=embed)
        else:
            if wait.content.lower() == logo.brand.lower():
                embed.title = "🎉 Good Job 🎉"
                embed.description = f"The answer was {logo.brand}"
                try:
                    embed.set_image(url=logo.answer)
                except discord.HTTPException:
                    pass
                return await message.edit(embed=embed)
            embed.title = f"{self.avi.emoji_dictionary['red_tick']} | Wrong"
            embed.description = f"Your answer was {wait.content}.\nThe correct answer is actually {logo.brand}"
            try:
                embed.set_image(url=logo.answer)
            except discord.HTTPException:
                pass
            await message.edit(embed=embed)

    @commands.command(
        name="roast",
        brief="Roasts a person. (Powered by Dagpi)")
    async def dag_roast(self, ctx: AvimetryContext, member: discord.Member):
        roast = await self.avi.dagpi.roast()
        await ctx.send(f"{member.mention}, {roast}")

    @commands.command(
        name="funfact",
        brief="Gets a random fun fact. (Powered by Dagpi)")
    async def dag_fact(self, ctx: AvimetryContext):
        fact = await self.avi.dagpi.fact()
        await ctx.send(fact)

    @commands.command(
        brief="Checks if a person is gay"
    )
    async def gay(self, ctx: AvimetryContext, member: discord.Member = None):
        if member is None:
            member = ctx.author
        conf = await ctx.confirm(f"Is {member.mention} gay?")
        if conf:
            return await ctx.send(f"{member.mention} is gay.")
        return await ctx.send(f"{member.mention} is not gay.")


def setup(avi):
    avi.add_cog(Fun(avi))
