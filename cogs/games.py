"""
Game commands
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
import datetime
import akinator
import typing
import asyncio
import random

from akinator.async_aki import Akinator
from discord.ext import commands
from utils import AvimetryContext, AvimetryBot, Timer
from utils import core


class Games(commands.Cog, name="Bot Info"):
    """
    Game commands
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now()

    @core.command(aliases=["\U0001F36A", "vookir", "kookie"])
    @commands.cooldown(5, 10, commands.BucketType.member)
    @commands.max_concurrency(2, commands.BucketType.channel)
    async def cookie(self, ctx: AvimetryContext, member: typing.Optional[discord.Member] = None):
        """
        Grab the cookie!

        Mentioning a person with this command will enter duel mode.
        This makes it so that only you can the person you mentioned can get the cookie.
        """
        if member == ctx.author:
            return await ctx.send("You can't play against yourself.")
        cookie_embed = discord.Embed(
            title="Get the cookie!",
            description="Get ready to grab the cookie!")
        cd_cookie = await ctx.send(embed=cookie_embed)
        await cd_cookie.edit(embed=cookie_embed)
        await asyncio.sleep(random.randint(1, 12))
        cookie_embed.title = "GO!"
        cookie_embed.description = "GET THE COOKIE NOW!"
        await cd_cookie.edit(embed=cookie_embed)
        await cd_cookie.add_reaction("\U0001F36A")

        if member:
            def check(reaction, user):
                return(
                    reaction.message.id == cd_cookie.id and
                    str(reaction.emoji) == "\U0001F36A" and
                    user in [ctx.author, member]
                )
        else:
            def check(reaction, user):
                return (
                    reaction.message.id == cd_cookie.id and
                    str(reaction.emoji) in "\U0001F36A" and
                    user != self.bot.user
                )

        try:
            with Timer() as reaction_time:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=check, timeout=10
                )
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

    async def remove(self, message: discord.Message, emoji, user, perm: bool):
        if not perm:
            return
        await message.remove_reaction(emoji, user)

    async def clear(self, message: discord.Message, perm: bool):
        if not perm:
            return
        await message.clear_reactions()

    @core.command(
        name="akinator",
        aliases=["aki", "avinator"])
    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.max_concurrency(1, commands.BucketType.channel)
    @core.bot_has_permissions(add_reactions=True)
    async def fun_akinator(self, ctx: AvimetryContext, mode="en"):
        """
        Play a game of akinator.

        This command has a high cooldown because a lot of reactions can cause ratelimits.
        Discord can be thanked for this.
        """
        ended = False
        bot_perm = ctx.me.permissions_in(ctx.channel)
        perms = True if bot_perm.manage_messages is True else False
        aki_dict = {
            "<:greentick:777096731438874634>": "yes",
            "<:redtick:777096756865269760>": "no",
            "\U0001f937": "idk",
            "\U0001f914": "probably",
            "\U0001f614": "probably not",
            "<:Back:815854941083664454>": "back",
            "<:Stop:815859174667452426>": "stop"
        }
        aki_react = list(aki_dict)
        aki_client = Akinator()
        akinator_embed = discord.Embed(
            title="Akinator",
            description="Starting Game..."
        )
        async with ctx.channel.typing():
            initial_messsage = await ctx.send(embed=akinator_embed)
            for reaction in aki_react:
                await initial_messsage.add_reaction(reaction)
            game = await aki_client.start_game(mode)

        while aki_client.progression <= 80:
            akinator_embed.description = game
            await initial_messsage.edit(embed=akinator_embed)

            def check(reaction, user):
                return (
                    reaction.message.id == initial_messsage.id and
                    str(reaction.emoji) in aki_react and
                    user == ctx.author and
                    user != self.bot.user
                )

            done, pending = await asyncio.wait([
                self.bot.wait_for("reaction_remove", check=check, timeout=20),
                self.bot.wait_for("reaction_add", check=check, timeout=20)
            ], return_when=asyncio.FIRST_COMPLETED)

            try:
                reaction, user = done.pop().result()

            except asyncio.TimeoutError:
                await self.clear(initial_messsage, perms)
                akinator_embed.description = (
                    "Akinator session closed because you took too long to answer."
                )
                ended = True

                await initial_messsage.edit(embed=akinator_embed)
                break
            else:
                ans = aki_dict[str(reaction.emoji)]
                if ans == "stop":
                    ended = True
                    akinator_embed.description = "Akinator session stopped."
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
            if ended:
                return
            await initial_messsage.delete()
            initial_messsage = await ctx.send("...")
        if ended:
            return
        await aki_client.win()

        akinator_embed.description = (
            f"I think it is {aki_client.first_guess['name']} ({aki_client.first_guess['description']})! Was I correct?"
        )
        akinator_embed.set_image(url=f"{aki_client.first_guess['absolute_picture_path']}")
        await initial_messsage.edit(embed=akinator_embed)
        reactions = ["<:greentick:777096731438874634>", "<:redtick:777096756865269760>"]
        for reaction in reactions:
            await initial_messsage.add_reaction(reaction)

        def yes_no_check(reaction, user):
            return (
                reaction.message.id == initial_messsage.id and
                str(reaction.emoji) in ["<:greentick:777096731438874634>", "<:redtick:777096756865269760>"] and
                user != self.bot.user and
                user == ctx.author
            )
        try:
            reaction, user = await self.bot.wait_for(
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

    @core.command(name="10s")
    @core.bot_has_permissions(add_reactions=True)
    async def _10s(self, ctx: AvimetryContext):
        """
        Test your reaction time.

        See how close you can get to 10 exactly seconds.
        """
        embed_10s = discord.Embed(
            title="10 seconds",
            description="Click the cookie in 10 seconds"
        )
        react_message = await ctx.send(embed=embed_10s)
        await react_message.add_reaction("\U0001F36A")

        def check_10s(reaction, user):
            return (
                reaction.message.id == react_message.id and str(reaction.emoji) in "\U0001F36A" and user == ctx.author
            )

        try:
            with Timer() as timer:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", check=check_10s, timeout=20
                )
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

    @core.command(
        name="guessthatlogo",
        aliases=["gtl"]
    )
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_guess_that_logo(self, ctx: AvimetryContext):
        """
        Try to guess the logo given to you.

        This command is powered by the Dagpi api.
        """
        async with ctx.channel.typing():
            logo = await self.bot.dagpi.logo()
        embed = discord.Embed(
            title="Which logo is this?",
            description=f"{logo.clue}"
        )
        embed.set_image(url=logo.question)
        message = await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author

        try:
            wait = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            embed.title = f"{self.bot.emoji_dictionary['red_tick']} | Time's Up!"
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
            embed.title = f"{self.bot.emoji_dictionary['red_tick']} | Wrong"
            embed.description = f"Your answer was {wait.content}.\nThe correct answer is actually {logo.brand}"
            try:
                embed.set_image(url=logo.answer)
            except discord.HTTPException:
                pass
            await message.edit(embed=embed)

    @core.command()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    @core.bot_has_permissions(add_reactions=True)
    async def reaction(self, ctx: AvimetryContext):
        """
        See how fast you can get the correct emoji.
        """
        emoji = ["🍪", "🎉", "🧋", "🍒", "🍑"]
        random_emoji = random.choice(emoji)
        random.shuffle(emoji)
        embed = discord.Embed(
            title="Reaction time",
            description="After 1-15 seconds I will reveal the emoji."
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
            return(
                reaction.message.id == first.id and str(reaction.emoji) == random_emoji and user != self.bot.user)

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


def setup(bot):
    bot.add_cog(Games(bot))
