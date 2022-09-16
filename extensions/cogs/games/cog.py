"""
[Ignition Bot]
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
from io import BytesIO
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from asyncakinator import Akinator

import core
from utils import Timer, Emojis
from .components import (
    CookieView,
    AkinatorFlags,
    AkinatorGameView,
    RPSView
)

if TYPE_CHECKING:
    from datetime import datetime
    from core import Bot, Context


class Games(core.Cog):
    """
    Game commands.
    """

    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.emoji: str = "\U0001f3ae"
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)

    @core.group(aliases=["\U0001F36A", "vookir", "kookie"])
    @core.cooldown(5, 10, commands.BucketType.member)
    @commands.max_concurrency(2, commands.BucketType.channel)
    async def cookie(self, ctx: Context, member: discord.Member | None = None):
        """
        Grab the cookie!

        Mentioning a person with this command will enter duel mode.
        This makes it so that only you can the person you mentioned can get the cookie.
        """
        if member == ctx.author:
            return await ctx.send("You can't play against yourself.")
        cookie_embed = discord.Embed(title="Get the cookie!", description="Get ready to grab the cookie!")
        cd_cookie = await ctx.send(embed=cookie_embed)
        await asyncio.sleep(random.randint(1, 12))
        cookie_embed.title = "GO!"
        cookie_embed.description = "GET THE COOKIE NOW!"
        await cd_cookie.edit(embed=cookie_embed)
        await cd_cookie.add_reaction("\U0001F36A")

        if member:
            def member_check(reaction: discord.Reaction, user: discord.Member | discord.User) -> bool:
                return (
                    reaction.message.id == cd_cookie.id
                    and str(reaction.emoji) == "\U0001F36A"
                    and user in [ctx.author, member]
                )
            check = member_check
        else:
            def check(reaction: discord.Reaction, user: discord.Member | discord.User):
                return (
                    reaction.message.id == cd_cookie.id
                    and str(reaction.emoji) in "\U0001F36A"
                    and user != self.bot.user
                )

        try:
            with Timer() as reaction_time:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=10)
        except asyncio.TimeoutError:
            cookie_embed.title = "Game over!"
            cookie_embed.description = "Nobody got the cookie :("
            await cd_cookie.edit(embed=cookie_embed)
            await cd_cookie.remove_reaction("\U0001F36A", ctx.me)
        else:
            if str(reaction.emoji) == "\U0001F36A":
                thing = reaction_time.total_time * 1000
                total_second = f"**{thing:.2f}ms**"
                if thing > 1000:
                    gettime = thing / 1000
                    total_second = f"**{gettime:.2f}s**"
                cookie_embed.title = "Nice!"
                cookie_embed.description = f"{user.mention} got the cookie in **{total_second}**"
                await cd_cookie.remove_reaction("\U0001F36A", ctx.me)
                return await cd_cookie.edit(embed=cookie_embed)

    @cookie.command()
    @core.cooldown(5, 10, commands.BucketType.member)
    @commands.max_concurrency(2, commands.BucketType.channel)
    async def button(self, ctx: Context):
        """
        Grab the cookie! (Button Edition)

        Just like the cookie command but it uses buttons instead of reactions.
        """
        view = CookieView(10, ctx)
        cookie_embed = discord.Embed(title="Get the cookie!", description="Get ready to grab the cookie!")
        cookie_message = await ctx.send(embed=cookie_embed)
        view.message = cookie_message
        await asyncio.sleep(random.randint(1, 12))
        cookie_embed.title = "GO!"
        cookie_embed.description = "GET THE COOKIE NOW!"
        await cookie_message.edit(embed=cookie_embed, view=view)
        with Timer() as timer:
            await view.wait()
        assert view.winner is not None
        thing = timer.total_time * 1000
        total_second = f"**{thing:.2f}ms**"
        if thing > 1000:
            gettime = thing / 1000
            total_second = f"**{gettime:.2f}s**"
        cookie_embed.title = "Nice!"
        cookie_embed.description = f"{view.winner.mention} got the cookie in **{total_second}**"
        return await cookie_message.edit(embed=cookie_embed, view=None)

    @core.command(hybrid=True, name="akinator", aliases=["aki"])
    @core.cooldown(1, 60, commands.BucketType.member)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def akinator(self, ctx: Context, *, flags: AkinatorFlags):
        """
        Play a game of akinator.
        """
        # Since you can edit your message to invoke commands,
        # the bot also edits messages and cause interaction errors.
        # This is a lazy workaround to prevent that.

        if flags.child is False and ctx.channel.is_nsfw() is False:
            return await ctx.send("Child mode must be enabled in non-NSFW channels.")

        message = None
        if ctx.message and ctx.message.edited_at:
            message = await ctx.send("Starting game...")
        akiclient = Akinator(language=flags.language, theme=flags.theme, child_mode=flags.child)
        async with ctx.typing():
            game = await akiclient.start()
            embed = discord.Embed(title="Akinator", description=f"{akiclient.step+1}. {game}")

        if message is not None:
            await message.delete()

        view = AkinatorGameView(member=ctx.author, ctx=ctx, client=akiclient, embed=embed)
        view.message = await ctx.send(embed=embed, view=view)

    @core.command(hybrid=True, aliases=["rps"])
    @commands.max_concurrency(1, commands.BucketType.channel)
    @core.cooldown(2, 5, commands.BucketType.member)
    @core.describe(opponent="Who you want to play against.")
    async def rockpaperscissors(self, ctx: Context, opponent: discord.Member | None = None):
        """
        Play a game of rock paper scissors.

        You can play against another person or against the bot if you don't provide an opponent.
        """
        opp = opponent or ctx.me

        if opp == ctx.author:
            return await ctx.send("You can't play against yourself.")
        if opp.bot and opp != ctx.me:
            return await ctx.send("You can't play against a bot.")

        embed = discord.Embed(
            title="Rock Paper Scissors",
            description=f"Who will win: {ctx.author.mention} or {opp.mention}?"
        )
        view = RPSView(embed=embed, context=ctx, opponent=opp)
        view.message = await ctx.send(embed=embed, view=view)

    @core.command(name="10s")
    @core.bot_has_permissions(add_reactions=True)
    async def _10s(self, ctx: Context):
        """
        Test your reaction time.

        See how close you can get to 10 exactly seconds.
        """
        embed_10s = discord.Embed(title="10 seconds", description="Click the cookie in 10 seconds")
        react_message = await ctx.send(embed=embed_10s)
        await react_message.add_reaction("\U0001F36A")

        def check_10s(reaction, user):
            return (
                reaction.message.id == react_message.id and str(reaction.emoji) in "\U0001F36A" and user == ctx.author
            )

        try:
            with Timer() as timer:
                reaction, user = await self.bot.wait_for("reaction_add", check=check_10s, timeout=20)
        except asyncio.TimeoutError:
            pass
        else:
            if str(reaction.emoji) == "\U0001F36A":
                final = timer.total_time
                if final < 5.0:
                    embed_10s.description = "Wait 10 seconds to get the cookie."
                    return await react_message.edit(embed=embed_10s)
                embed_10s.description = (
                    f"You got the cookie in {final:.2f} seconds with {(final-10)*1000:.2f}ms reaction time\n"
                )
                if final < 9.99:
                    embed_10s.description = f"You got the cookie in {final:.2f} seconds"
                await react_message.edit(embed=embed_10s)

    @core.command(name="guessthatlogo", aliases=["gtl"])
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_guess_that_logo(self, ctx: Context):
        """
        Try to guess the logo given to you.

        This command is powered by the Dagpi API.
        """
        async with ctx.channel.typing():
            logo = await self.bot.dagpi.logo()
            im = await self.bot.session.get(logo.question)
            read = await im.read()
            image_file = discord.File(BytesIO(read), filename="question.png")
        embed = discord.Embed(title="Which logo is this?", description=f"{logo.clue}")
        embed.set_image(url="attachment://question.png")
        message = await ctx.send(file=image_file, embed=embed)

        def check(m):
            return m.author == ctx.author

        try:
            wait = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            embed.title = f"{Emojis.RED_TICK} | Time's Up!"
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
            embed.title = f"{Emojis.RED_TICK} | Wrong"
            embed.description = f"Your answer was {wait.content}.\nThe correct answer is actually {logo.brand}"
            try:
                embed.set_image(url=logo.answer)
            except discord.HTTPException:
                pass
            await message.edit(embed=embed)

    @core.command()
    @core.cooldown(1, 10, commands.BucketType.channel)
    @core.bot_has_permissions(add_reactions=True)
    async def reaction(self, ctx: Context):
        """
        See how fast you can get the correct emoji.
        """
        emoji = ["🍪", "🎉", "🧋", "🍒", "🍑"]
        random_emoji = random.choice(emoji)
        random.shuffle(emoji)
        embed = discord.Embed(
            title="Reaction time",
            description="After 1-15 seconds I will reveal the emoji.",
        )
        first = await ctx.send(embed=embed)
        for react in emoji:
            await first.add_reaction(react)
        await asyncio.sleep(2.5)
        embed.description = "Get ready!"
        await first.edit(embed=embed)
        await asyncio.sleep(random.randint(1, 15))
        embed.description = f"GET THE {random_emoji} EMOJI!"
        await first.edit(embed=embed)

        def check(reaction, user):
            return reaction.message.id == first.id and str(reaction.emoji) == random_emoji and user != self.bot.user

        try:
            with Timer() as timer:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=15)
        except asyncio.TimeoutError:
            embed.description = "Timeout"
            await first.edit(embed=embed)
        else:
            if str(reaction.emoji) == random_emoji:
                gettime = timer.total_time * 1000
                total_second = f"**{gettime:.2f}ms**"
                if gettime > 1000:
                    gettime = gettime / 1000
                    total_second = f"**{gettime:.2f}s**"
                embed.description = f"{user.mention} got the {random_emoji} in {total_second}"
                return await first.edit(embed=embed)
