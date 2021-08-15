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
import typing
import asyncio
import random
import core

from akinator.async_aki import Akinator
from akinator import CantGoBackAnyFurther
from discord.ext import commands, menus
from utils import AvimetryContext, AvimetryBot, Timer


class AkinatorMenu(menus.Menu):
    def __init__(self, timeout=20, *, ctx, akiclient, embed):
        super().__init__(timeout=timeout, clear_reactions_after=True)
        self.ctx = ctx
        self.akiclient = akiclient
        self.embed = embed
        self.ended = False

    async def send_initial_message(self, ctx, channel):
        return await ctx.send(embed=self.embed)

    async def answer(self, answer):
        if answer == 'back':
            try:
                next = await self.akiclient.back()
                self.embed.description = f'{self.akiclient.step+1}. {next}'
                await self.message.edit(embed=self.embed)
            except CantGoBackAnyFurther:
                pass
        elif self.akiclient.progression <= 80:
            next = await self.akiclient.answer(answer)
            self.embed.description = f'{self.akiclient.step+1}. {next}'
            self.embed.set_footer(text=f"{self.akiclient.progression:,.2f}%")
            await self.message.edit(embed=self.embed)
        else:
            await self.akiclient.win()
            client = self.akiclient
            embed = discord.Embed(
                title='Akinator',
                description=(
                    f'Are you thinking of {client.first_guess["name"]} ({client.first_guess["description"]})?\n'
                )
            )
            embed.set_image(url=client.first_guess["absolute_picture_path"])
            await self.message.edit(embed=embed)

    @menus.button("<:greentick:777096731438874634>")
    async def yes(self, payload):
        await self.answer('yes')

    @menus.button("<:redtick:777096756865269760>")
    async def no(self, payload):
        await self.answer('no')

    @menus.button("\U0001f937")
    async def idk(self, payload):
        await self.answer('idk')

    @menus.button("\U0001f914")
    async def proabably(self, payload):
        await self.answer('probably')

    @menus.button("\U0001f614")
    async def proabably_not(self, payload):
        await self.answer('probably not')

    @menus.button("<:Back:815854941083664454>")
    async def back(self, payload):
        await self.answer('back')

    @menus.button("<:Stop:815859174667452426>")
    async def stop(self, payload):
        await self.akiclient.win()
        await self.akiclient.close()
        await self.message.edit("Game stopped.", embed=None)
        await super().stop(payload)


class Games(core.Cog):
    """
    Game commands.
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)

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
        aki_client = Akinator()
        async with ctx.channel.typing():
            game = await aki_client.start_game()
            embed = discord.Embed(title='Akinator', description=f'{aki_client.step+1}. {game}')
            embed.set_footer(text=f"{aki_client.progression:,.2f}%")
        menu = AkinatorMenu(ctx=ctx, akiclient=aki_client, embed=embed)
        await menu.start(ctx)

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
