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
import asyncio
import typing
import datetime

from utils import core
from aiogtts import aiogTTS
from io import BytesIO
from discord.ext import commands
from utils import AvimetryBot, AvimetryContext


class Fun(commands.Cog):
    """
    Fun commands for you and friends.
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now()
        self._cd = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.user)

    async def do_mock(self, string: str):
        return "".join(random.choice([mock.upper, mock.lower])() for mock in string)

    @core.command(aliases=["8ball", "8b"])
    @commands.cooldown(5, 15, commands.BucketType.member)
    async def eightball(self, ctx: AvimetryContext, *, question):
        """
        Ask the magic 8 ball a question.

        This command is not meant for actual advice.
        """
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
        if ctx.author.id in self.bot.owner_ids and question.lower().endswith(
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

    @core.command(aliases=["murder"])
    @commands.cooldown(2, 30, commands.BucketType.member)
    async def kill(self, ctx: AvimetryContext, member: discord.Member):
        """
        Kill some people.

        Be careful, You might accidentally kill yourself instead.
        """
        if member == self.bot.user or member.bot:
            await ctx.send("Nope.")
        elif member == ctx.author:
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
                f"{author} was caught by the police because they posted his plans to kill {member}",
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

    @core.command()
    @commands.cooldown(1, 120, commands.BucketType.member)
    async def say(self, ctx: AvimetryContext, *, message):
        """
        Makes me say something.

        This command has a high cooldown to prevent abuse.
        """
        await ctx.no_reply(message)

    @core.command()
    @commands.cooldown(1, 120, commands.BucketType.member)
    @core.has_permissions(manage_messages=True)
    async def dsay(self, ctx: AvimetryContext, *, message):
        """
        Same as say, but I delete your message also.

        This command has a high cooldown to prevent abuse.
        """
        await ctx.message.delete()
        await ctx.no_reply(message)

    @core.command()
    @core.bot_has_permissions(manage_webhooks=True)
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def copy(self, ctx: AvimetryContext, member: typing.Union[discord.User, discord.Member], *, text):
        """
        Makes it look like a person said something.

        This makes use of a webhook, That's why a "BOT" tag shows next to their name.
        This is a Discord limitation.
        """
        if member == self.bot.user:
            say = self.bot.get_command("say")
            return await say(ctx, message=text)
        webhooks = await ctx.channel.webhooks()
        avimetry_webhook = discord.utils.get(webhooks, name="Avimetry")
        if not avimetry_webhook:
            avimetry_webhook = await ctx.channel.create_webhook(
                name="Avimetry", reason="For Avimetry copy command.",
                avatar=await self.bot.user.avatar_url.read())
        await avimetry_webhook.send(
            text, username=member.display_name,
            avatar_url=member.avatar_url_as(format="png"),
            allowed_mentions=discord.AllowedMentions.none())

    @core.command(
        aliases=["fp", "facep", "fpalm"]
    )
    async def facepalm(self, ctx: AvimetryContext, member: discord.Member = None):
        """
        Sends a message saying you hit your head.
        """
        if member is None:
            return await ctx.send(f"{ctx.author.mention} facepalmed.")
        return await ctx.send(f"{ctx.author.mention} facepalmed because {member.mention} was being stupid.")

    @core.command()
    async def skin(self, ctx: AvimetryContext, member: discord.Member):
        """
        Sends a message saying you skinned someone.

        Why? Because furries.
        """
        await ctx.message.delete()
        if member == ctx.author:
            c = discord.Embed(description="You can't skin yourself, stupid")
            await ctx.send(embed=c)
        else:
            e = discord.Embed(description=f"{member.mention} was skinned.")
            await ctx.send(embed=e)

    @core.command(aliases=["sd"])
    async def selfdestruct(self, ctx: AvimetryContext):
        """
        Self desctruct?!?!! Who put that there?!!?
        """
        if await self.bot.is_owner(ctx.author):
            command = self.bot.get_command('dev reboot')
            return await command(ctx)
        a = discord.Embed(
            description=f"{ctx.author.mention} self destructed due to overloaded fuel canisters")
        await ctx.send(embed=a)

    @core.command()
    async def dropkick(self, ctx: AvimetryContext, *, mention: discord.Member):
        """
        Sends a message saying you dropped kicked someone.

        Funny am I right?
        """
        if mention == ctx.author:
            embed = discord.Embed(description=f"{ctx.author.mention} drop kicked themselves. Amazing.")
        else:
            embed = discord.Embed(
                description=f"{ctx.author.mention} dropkicked {mention.mention}, killing them.")
        await ctx.send(embed=embed)

    @core.command()
    async def ship(self, ctx: AvimetryContext, person1: discord.Member, person2: discord.Member):
        """
        Check if someone is compatible with someone.
        """
        if 750135653638865017 in (person1.id, person2.id):
            return await ctx.send(f"{person1.mention} and {person2.mention} are 0% compatible with each other")
        if person1 == person2:
            return await ctx.send("That's not how that works")
        percent = random.randint(0, 100)
        await ctx.send(f"{person1.mention} and {person2.mention} are {percent}% compatible with each other")

    @core.command(aliases=["pp", "penis", "penissize"])
    async def ppsize(self, ctx: AvimetryContext, member: discord.Member = None):
        """
        Get the person's pp size. Why not?
        """
        member = member or ctx.author
        pp_embed = discord.Embed(
            title=f"{member.name}'s pp size",
            description=f"8{'=' * random.randint(0, 12)}D"
        )
        await ctx.send(embed=pp_embed)

    @core.command()
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def reddit(self, ctx: AvimetryContext, subreddit):
        """
        Gets a random post from a subreddit you provide.

        NSFW posts will automatically show in NSFW channels. Otherwise it will give you an error.
        """
        if subreddit.startswith("r/"):
            subreddit = subreddit.replace("r/", "")
        async with self.bot.session.get(f"https://www.reddit.com/r/{subreddit}.json") as content:
            if content.status == 404:
                return await ctx.send("This subreddit does not exist. Please check your spelling and try again.")
            if content.status != 200:
                return await ctx.send("There has been a problem at Reddit. Please try again later.")
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
            if ctx.channel.is_nsfw():
                return await ctx.send(embed=embed)
            else:
                return await ctx.send("NSFW posts can't be send in non-nsfw channels.")
        return await ctx.send(embed=embed)

    @core.command()
    @commands.cooldown(1, 15, commands.BucketType.member)
    async def meme(self, ctx: AvimetryContext):
        """
        Get a meme from Reddit.

        This will get a meme from either the r/memes or r/meme subreddits.
        """
        reddit = self.bot.get_command("reddit")
        subreddits = ["memes", "meme"]
        await reddit(ctx, subreddit=random.choice(subreddits))

    @core.command(name="roast")
    async def dag_roast(self, ctx: AvimetryContext, member: discord.Member):
        """
        Roasts a person. May be offensive/NSFW.

        These roasts come from the Dagpi api.
        """
        roast = await self.bot.dagpi.roast()
        await ctx.send(f"{member.mention}, {roast}")

    @core.command(name="funfact", aliases=["fact"])
    async def dag_fact(self, ctx: AvimetryContext):
        """
        Get a fun fact.

        These facts are taken from the Dagpi api.
        """
        fact = await self.bot.dagpi.fact()
        await ctx.send(fact)

    @core.command()
    async def gay(self, ctx: AvimetryContext, member: discord.Member = None):
        """
        Is a person gay? This is up to you.
        """
        if member is None:
            member = ctx.author
        conf = await ctx.confirm(f"Is {member.mention} gay?")
        if conf:
            return await ctx.send(f"{member.mention} is gay.")
        return await ctx.send(f"{member.mention} is not gay.")

    @core.command()
    async def gayrate(self, ctx: AvimetryContext, member: discord.Member = None):
        """
        Check how gay a person is.

        This command picks a random number from 1-100.
        """
        if member is None:
            member = ctx.author
        if await self.bot.is_owner(member):
            return await ctx.send(f"{member.mention} is **{random.randint(0, 10)}%** gay :rainbow:")
        return await ctx.send(f"{member.mention} is **{random.randint(10, 100)}%** gay :rainbow:")

    @core.command()
    async def height(self, ctx: AvimetryContext):
        """
        This command tells you how tall you are.

        No need to thank us.
        """
        await ctx.send("How tall are you? (Ex: 1'4\")")

        def check(message: discord.Message):
            return message.author == ctx.author and message.channel == ctx.channel
        try:
            height = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("You didn't respond in time!")
        else:
            embed = discord.Embed(
                title="Height",
                description=f"You are {height.content}!"
            )
            embed.set_footer(text="No need to thank me.")
            await ctx.send(embed=embed)

    @core.command()
    async def clap(self, ctx: AvimetryContext, *, words):
        """
        Adds the 👏 emoji between each word you provide

        Example: 👏 do 👏 not 👏 do 👏 that 👏
        """
        input = words.split(" ")
        output = f"👏 {' 👏 '.join(input)} 👏"
        await ctx.send(output)

    @core.command()
    async def recursion(self, ctx: AvimetryContext):
        """
        Did you mean recursion?
        """
        embed = discord.Embed(
            title="Invalid Command",
            description='"recursion" was not found. Did you mean...\n`recursion`'
        )
        embed.set_footer(text=f'Use {ctx.prefix}help to see the whole list of commands.')
        await ctx.send(embed=embed)

    @core.command()
    async def tts(self, ctx: AvimetryContext, *, text):
        """
        Text to speech!

        Takes your text and converts to audio and sends it to the channel
        """
        async with ctx.channel.typing():
            aiogtts = aiogTTS()
            buffer = BytesIO()
            await aiogtts.write_to_fp(text, buffer, lang='en')
            buffer.seek(0)
            file = discord.File(buffer, f"{ctx.author.name}-tts.mp3")
        await ctx.send(file=file)

    @core.command(user_permissions='manage_messages')
    async def aaa(self, ctx: AvimetryContext):
        await ctx.send('a')


def setup(bot):
    bot.add_cog(Fun(bot))
