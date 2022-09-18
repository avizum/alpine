"""
[Avimetry Bot]
Copyright (C) 2021 - 2022 avizum

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

from __future__ import annotations

import asyncio
import datetime as dt
import random
from base64 import b64decode
from io import BytesIO
from typing import Literal, TYPE_CHECKING

import discord
from aiogtts import aiogTTS
from discord.ext import commands

import core

if TYPE_CHECKING:
    from datetime import datetime
    from core import Bot, Context
    from discord.ext.commands import CooldownMapping


TikTokTTSOptions = Literal[
    "Ghost Face",
    "Chewbacca",
    "C3PO",
    "Stitch",
    "Stormtrooper",
    "Rocket",
    "English F AU",
    "English M AU",
    "English M UK",
    "English F US",
    "English M 1 US",
    "English M 2 US",
    "English M 3 US",
    "English M 4 US",
    "French M",
    "German F",
    "Spanish M",
    "Portuguese BR F",
    "Indonesian F",
    "Japanese F",
    "Korean F",
    "Narrator",
    "Singing F Alto",
    "Singing M Tenor",
]

tiktok_tts_mapping: dict[str, str] = {
    "Ghost Face": "en_us_ghostface",
    "Chewbacca": "en_us_chewbacca",
    "C3PO": "en_us_c3po",
    "Stitch": "en_us_stitch",
    "Stormtrooper": "en_us_stormtrooper",
    "Rocket": "en_us_rocket",
    "English F AU": "en_au_001",
    "English M AU": "en_au_002",
    "English M 1 UK": "en_uk_001",
    "English F US": "en_us_001",
    "English M 1 US": "en_us_006",
    "English M 2 US": "en_us_007",
    "English M 3 US": "en_us_009",
    "English M 4 US": "en_us_010",
    "French M": "fr_001",
    "German F": "de_001",
    "Spanish M": "es_002",
    "Portuguese BR F": "br_001",
    "Indonesian F": "id_001",
    "Japanese F": "jp_001",
    "Korean F": "kr_003",
    "Narrator": "en_male_nattation",
    "Singing F Alto": "en_female_f08_salut_damour",
    "Singing M Tenor": "en_male_m03_lobby",
}


class Fun(core.Cog):
    """
    Fun commands for you and friends.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.emoji: str = "\U0001f3b1"
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)
        self._cd: CooldownMapping = commands.CooldownMapping.from_cooldown(1.0, 60.0, commands.BucketType.user)

    @core.command(aliases=["8ball", "8b"])
    @core.cooldown(5, 15, commands.BucketType.member)
    async def eightball(self, ctx: Context, *, question: str):
        """
        Ask the magic 8 ball a question.

        This command is not meant for actual advice.
        """
        responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most Likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Certainly.",
            "Very certain.",
            "Absolutely.",
            "Definitely",
            "Yeah.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better tell you later.",
            "Better not tell you now.",
            "Can not predict now.",
            "Concentrate and ask again.",
            "Go away.",
            f"Try again {ctx.author.display_name}.",
            "THINK HARDER AND TRY AGAIN.",
            "You again?",
            "No.",
            "As I see it, no.",
            "Don't count on it.",
            "My reply is no.",
            "No, definately not.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
            "You have got to be kidding me.",
            "Oh God, NO.",
        ]
        ballembed = discord.Embed(title=":8ball: Magic 8 Ball")
        ballembed.add_field(name="Question:", value=f"{question}", inline=False)
        ballembed.add_field(name="Answer:", value=f"{random.choice(responses)}", inline=False)
        await ctx.send(embed=ballembed)

    @core.command(aliases=["murder"])
    @core.cooldown(2, 30, commands.BucketType.member)
    async def kill(self, ctx: Context, member: discord.Member):
        """
        Kill some people.

        Be careful, You might accidentally kill yourself instead.
        """
        if member == self.bot.user or member.bot:
            await ctx.send("Nope.")
        elif member == ctx.author:
            await ctx.send("You're funny.")
        else:
            author = ctx.author.mention
            target = member.mention
            kill_response = [
                f"{author} killed {target}.",
                f"{author} murdered {target} with a machine gun.",
                f"{author} accidentally shot themselves in the face while trying to load the gun.",
                f"{author} died while summoning a demon to kill {target}",
                f"{target} summoned a demon to kill {author}.",
                f"{author} was caught by the police because they posted his plans to kill {target}",
                f"{author} hired a hitman to kill {target}.",
                f"{author} shot {target}. While reloading the gun, {author} shot themselves on the head.",
                f"{author} kidnapped {target} and chopped their head off with a guillotine",
                f"{author} sniped {target} at the store.",
                f"{author} tried to poison {target} but {author} put the poison in their drink.",
                f"{author} died whilst fighting {target}.",
                f"{target} was stoned to death by {author}.",
                f"{target} was almost killed by {author} but {target} took the gun and shot {author}",
            ]
            await ctx.send(f"{random.choice(kill_response)}")

    @core.command()
    @core.cooldown(1, 120, commands.BucketType.member)
    async def say(self, ctx: Context, *, message: str):
        """
        Makes me say something.

        This command has a high cooldown to prevent abuse.
        """
        await ctx.send(message)

    @core.command()
    async def mock(self, ctx: Context, *, message: str):
        """
        Make text like ThIs.
        """
        return await ctx.send("".join(random.choice([mock.upper, mock.lower])() for mock in message))


    @core.command()
    async def dropkick(self, ctx: Context, *, mention: discord.Member):
        """
        Sends a message saying you dropped kicked someone.

        Funny am I right?
        """
        if mention == ctx.author:
            embed = discord.Embed(description=f"{ctx.author.mention} drop kicked themselves. Amazing.")
        else:
            embed = discord.Embed(description=f"{ctx.author.mention} dropkicked {mention.mention}.")
        await ctx.send(embed=embed)

    @core.command()
    async def ship(self, ctx: Context, person1: discord.Member, person2: discord.Member):
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
    async def ppsize(self, ctx: Context, member: discord.Member | None = None):
        """
        Get the person's pp size. Why not?
        """
        member = member or ctx.author
        pp_embed = discord.Embed(
            title=f"{member.name}'s pp size",
            description=f"8{'=' * random.randint(1, 12)}D",
        )
        await ctx.send(embed=pp_embed)

    @core.command()
    @core.cooldown(1, 15, commands.BucketType.member)
    async def reddit(self, ctx: Context, subreddit: str):
        """
        Gets a random post from a subreddit you provide.

        NSFW posts will automatically show in NSFW channels.
        If the channel is not NSFW, it will not show.
        """
        if subreddit.startswith("r/"):
            subreddit = subreddit.replace("r/", "")
        async with self.bot.session.get(f"https://www.reddit.com/r/{subreddit}.json") as content:
            if content.status == 404:
                return await ctx.send("Could not find that subreddit. Please check your spelling and try again.")
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
            description=desc,
        )
        url = data["url"]
        embed.set_image(url=url)
        embed.add_field(
            name="Post Info:",
            value=(
                f"<:upvote:818730949662867456> {data['ups']} "
                f"<:downvote:818730935829659665> {data['downs']}\n"
                f"Upvote ratio: {data['upvote_ratio']}\n"
            ),
        )
        if data["over_18"]:
            if ctx.channel.is_nsfw():
                return await ctx.send(embed=embed)
            return await ctx.send("NSFW posts can't be sent in non-nsfw channels.")
        return await ctx.send(embed=embed)

    @core.command()
    @core.cooldown(1, 15, commands.BucketType.member)
    async def meme(self, ctx: Context):
        """
        Get a meme from Reddit.

        This fetches a meme from the r/memes and r/meme subreddits.
        """
        subreddits = ["memes", "meme"]
        await ctx.invoke(self.reddit, random.choice(subreddits))

    @core.command(name="roast")
    async def dag_roast(self, ctx: Context, member: discord.Member):
        """
        Roasts a person. May be offensive/NSFW.

        These roasts come from the Dagpi API.
        """
        roast = await self.bot.dagpi.roast()
        await ctx.send(f"{member.mention}, {roast}")

    @core.command(name="funfact", aliases=["fact"])
    async def dag_fact(self, ctx: Context):
        """
        Get a fun fact.

        These facts are taken from the Dagpi API.
        """
        fact = await self.bot.dagpi.fact()
        await ctx.send(fact)

    @core.command(aliases=["gaymeter"])
    async def gayrate(self, ctx: Context, member: discord.Member | None = None):
        """
        Check how gay a person is.

        This command picks a random number from 1-100.
        """
        member = member or ctx.author
        if await self.bot.is_owner(member):
            return await ctx.send(f"{member.mention} is **{random.randint(0, 10)}%** gay :rainbow:")
        return await ctx.send(f"{member.mention} is **{random.randint(10, 100)}%** gay :rainbow:")

    @core.command()
    async def height(self, ctx: Context):
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
            embed = discord.Embed(title="Height", description=f"You are {height.content}!")
            embed.set_footer(text="No need to thank me.")
            await ctx.send(embed=embed)

    @core.command()
    async def clap(self, ctx: Context, *, words):
        """
        Adds the 👏 emoji between each word you provide

        Example: 👏 do 👏 not 👏 do 👏 that 👏
        """
        inp = words.split(" ")
        output = f"👏 {' 👏 '.join(inp)} 👏"
        await ctx.send(output)

    @core.group(invoke_without_command=True, hybrid=True)
    async def tts(self, ctx: Context):
        """
        Text to speech commands.

        All functionality is found within its subcommands.
        """
        await ctx.send_help(ctx.command)

    @tts.command()
    @core.cooldown(1, 60, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def google(self, ctx: Context, *, text: str):
        """
        Text to speech!

        Takes your text and converts to audio and sends it to the channel
        """
        async with ctx.typing():
            aiogtts = aiogTTS()
            buffer = BytesIO()
            await aiogtts.write_to_fp(text, buffer, lang="en")
            buffer.seek(0)
            file = discord.File(buffer, f"{ctx.author.name}-google-tts.mp3")
        await ctx.send(file=file)

    @tts.command()
    @core.cooldown(1, 60, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def tiktok(
        self,
        ctx: Context,
        voice: TikTokTTSOptions = "English F US",
        *,
        text: str,
    ):
        """
        Takes your text and converts to audio from TikTok.
        """
        voice_type = tiktok_tts_mapping[voice]
        async with ctx.typing():
            info = await self.bot.session.post(
                "https://api16-normal-useast5.us.tiktokv.com/media/api/text/speech/invoke/",
                data={
                    "text_speaker": voice_type,
                    "req_text": text,
                    "speaker_map_type": 0,
                },
            )
            buffer = BytesIO(b64decode([(await info.json())["data"]["v_str"]][0]))
            buffer.seek(0)

            file = discord.File(buffer, f"{ctx.author.name}-tiktok-tts.mp3")
        await ctx.send(file=file)
