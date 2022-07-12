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

import asyncio
import contextlib
import datetime
import random

from io import BytesIO

import discord
import roblox
from discord.ext import commands
from akinator.async_aki import Akinator

import core
from core import Bot, Context
from utils import Timer, Emojis
from .components import (
    CookieView,
    AkinatorFlags,
    AkinatorGameView,
    RockPaperScissorGame,
)


class Games(core.Cog):
    """
    Game commands.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.emoji = "\U0001f3ae"
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.rclient = roblox.Client(self.bot.settings["api_tokens"]["Roblox"])

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

            def check(reaction, user):
                return (
                    reaction.message.id == cd_cookie.id
                    and str(reaction.emoji) == "\U0001F36A"
                    and user in [ctx.author, member]
                )

        else:

            def check(reaction, user):
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
    async def button(self, ctx):
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
        message = None
        if ctx.message and ctx.message.edited_at:
            message = await ctx.send("Starting game...")
        akiclient = Akinator()
        mode_map = {"default": "en", "animals": "en_animals", "objects": "en_objects"}
        async with ctx.typing():
            game = await akiclient.start_game(language=mode_map[flags.mode], child_mode=flags.child)
            if akiclient.child_mode is False and ctx.channel.nsfw is False:
                return await ctx.send("Child mode can only be disabled in NSFW channels.")
            embed = discord.Embed(title="Akinator", description=f"{akiclient.step+1}. {game}")

        if message is not None:
            await message.delete()

        view = AkinatorGameView(member=ctx.author, ctx=ctx, client=akiclient, embed=embed)
        view.message = await ctx.send(embed=embed, view=view)

    @core.command(aliases=["rps"])
    @commands.max_concurrency(1, commands.BucketType.channel)
    @core.cooldown(2, 5, commands.BucketType.member)
    async def rockpaperscissors(self, ctx: Context):
        """
        Play a game of rock paper scissors.
        """
        embed = discord.Embed(title="Rock Paper Scissors", description="Who will win?")
        view = RockPaperScissorGame(ctx=ctx, member=ctx.author, embed=embed)
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

    @core.group()
    async def roblox(self, ctx: Context):
        """
        Base command for all the ROBLOX commands.

        All functionality is found in the subcommands.
        """
        await ctx.send_help(ctx.command)

    @roblox.group()
    async def user(self, ctx: Context, name_or_id: str | int):
        """
        Gets ROBLOX User Information.
        """
        async with ctx.channel.typing():
            user = None
            with contextlib.suppress(roblox.UserNotFound):
                user = await self.rclient.get_user_by_username(name_or_id)
            with contextlib.suppress(roblox.UserNotFound):
                user = await self.rclient.get_user(name_or_id)

            if user:
                embed = discord.Embed(title=f"Roblox User: {user.name}")
                embed.add_field(name="Display Name", value=user.display_name, inline=True)
                embed.add_field(name="User ID", value=user.id, inline=True)
                embed.add_field(
                    name="Description",
                    value=user.description or "No Description",
                    inline=False,
                )
                embed.add_field(
                    name="Status",
                    value=await user.get_status() or "No Status",
                    inline=True,
                )
                pres = await user.get_presence()
                presence = pres.last_location or "Not Found"
                embed.add_field(name="Last Location", value=presence, inline=True)
                embed.add_field(name="Friends", value=await user.get_friend_count(), inline=True)
                embed.add_field(name="Followers", value=await user.get_follower_count(), inline=True)
                embed.add_field(
                    name="Following",
                    value=await user.get_following_count(),
                    inline=True,
                )
                past = [username_history async for username_history in user.username_history(max_items=10)]
                if past:
                    embed.add_field(name="Past Usernames", value=", ".join(past), inline=True)
                else:
                    embed.add_field(name="\u200b", value="\u200b", inline=True)
                embed.add_field(
                    name="Join Date",
                    value=discord.utils.format_dt(user.created),
                    inline=True,
                )
                embed.add_field(
                    name="Last Online",
                    value=discord.utils.format_dt(pres.last_online),
                    inline=True,
                )
                user_thumbnails = await self.rclient.thumbnails.get_user_avatar_thumbnails(
                    users=[user],
                    type=roblox.AvatarThumbnailType.headshot,
                    size=(100, 100),
                )
                if len(user_thumbnails) > 0:
                    user_thumbnail = user_thumbnails[0]
                    embed.set_thumbnail(url=user_thumbnail.image_url)
                user_thumbnails = await self.rclient.thumbnails.get_user_avatar_thumbnails(
                    users=[user],
                    type=roblox.AvatarThumbnailType.full_body,
                    size=(250, 250),
                )
                if len(user_thumbnails) > 0:
                    user_thumbnail = user_thumbnails[0]
                    embed.set_image(url=user_thumbnail.image_url)
                return await ctx.send(embed=embed)
            return await ctx.send("Could not find any users.")

    @user.command()
    async def search(self, ctx: Context, *, query: int | str):
        try:
            a = await self.rclient.get_users(query) or await self.rclient.get_users_by_usernames(query)
            await ctx.send(a)
        except Exception as e:
            await ctx.send(e)
