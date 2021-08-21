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

from discord.ext import commands
from akinator.async_aki import Akinator
from akinator import CantGoBackAnyFurther
from utils import AvimetryContext, AvimetryBot, Timer


class AkinatorConfirmView(discord.ui.View):
    def __init__(self, timeout=20, *, message, embed):
        super().__init__(timeout=timeout)
        self.message = message
        self.embed = embed

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, button, interaction):
        self.embed.description = f"{self.embed.description}\n---\nNice!"
        await self.message.edit(embed=self.embed, view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, button, interaction):
        self.embed.description = f"{self.embed.description}\n---\nAww, Maybe next time!"
        await self.message.edit(embed=self.embed, view=None)


class AkinatorGameView(discord.ui.View):
    def __init__(self, timeout=20, *, ctx, akiclient, member, embed):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.akiclient = akiclient
        self.member = member
        self.embed = embed
        self.ended = False

    async def on_error(self, error, item, interaction):
        await self.ctx.send(error)

    async def stop(self, *args, **kwargs):
        await self.akiclient.close()
        await self.message.edit(*args, **kwargs, view=None)
        super().stop()

    async def on_timeout(self):
        self.embed.description = 'Game ended due to timeout.'
        await self.stop(embed=self.embed)

    async def interaction_check(self, interaction):
        if interaction.user == self.member:
            return True
        else:
            await interaction.response.send_message(f'Only {self.member.mention} can play this.', ephemeral=True)

    async def answer(self, interaction, answer):
        if answer == 'back':
            try:
                next = await self.akiclient.back()
                self.embed.description = f'{self.akiclient.step+1}. {next}'
                await interaction.response.edit_message(embed=self.embed)
            except CantGoBackAnyFurther:
                await interaction.response.send_message('You can not go back any further.', ephemeral=True)
        elif self.akiclient.progression <= 80:
            await interaction.response.defer()
            next = await self.akiclient.answer(answer)
            self.embed.description = f'{self.akiclient.step+1}. {next}'
            await self.message.edit(embed=self.embed)
        else:
            await self.akiclient.win()
            client = self.akiclient
            self.embed.description = (
                f'Are you thinking of {client.first_guess["name"]} ({client.first_guess["description"]})?\n'
            )
            self.embed.set_image(url=client.first_guess["absolute_picture_path"])
            new_view = AkinatorConfirmView(message=self.message, embed=self.embed)
            await self.stop()
            await self.message.edit(view=new_view, embed=self.embed)

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.success, row=1)
    async def game_yes(self, button: discord.Button, interaction: discord.Interaction):
        await self.answer(interaction, 'no')

    @discord.ui.button(label='No', style=discord.ButtonStyle.danger, row=1)
    async def game_no(self, button: discord.Button, interaction: discord.Interaction):
        await self.answer(interaction, 'no')

    @discord.ui.button(label='I dont know', style=discord.ButtonStyle.primary, row=1)
    async def game_idk(self, button: discord.Button, interaction: discord.Interaction):
        await self.answer(interaction, 'i dont know')

    @discord.ui.button(label='Probably', style=discord.ButtonStyle.secondary, row=2)
    async def game_probably(self, button: discord.Button, interaction: discord.Interaction):
        await self.answer(interaction, 'probably')

    @discord.ui.button(label='Probably Not', style=discord.ButtonStyle.secondary, row=2)
    async def game_probably_not(self, button: discord.Button, interaction: discord.Interaction):
        await self.answer(interaction, 'probably not')

    @discord.ui.button(label='Back', style=discord.ButtonStyle.secondary, row=3)
    async def game_back(self, button: discord.Button, interaction: discord.Interaction):
        await self.answer(interaction, 'back')

    @discord.ui.button(label='Stop', style=discord.ButtonStyle.danger, row=3)
    async def game_stop(self, button: discord.Button, interaction: discord.Interaction):
        await self.akiclient.win()
        self.embed.description = 'Game stopped.'
        await interaction.response.edit_message(embed=self.embed, view=None)
        await self.stop()


class AkinatorFlags(commands.FlagConverter):
    mode: str = 'en'
    child: bool = True


class RockPaperScissorGame(discord.ui.View):
    def __init__(self, timeout=8, *, ctx, member, embed, player):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.p1 = member
        self.p2 = player
        self.embed = embed

    async def stop(self):
        for i in self.children:
            print(i.custom_id)
            i.disabled = True
        await self.message.edit(view=self)

    async def on_timeout(self):
        await self.stop()

    async def interaction_check(self, interaction):
        if interaction.user == self.member:
            return True
        else:
            await interaction.response.send_message(f'Only {self.member.mention} can play this.', ephemeral=True)

    async def answer(self, button, interaction, answer):
        await interaction.response.defer()

        game = {0: "**Rock**", 1: "**Paper**", 2: "**Scissors**"}
        key = [
            [0, 1, -1],
            [-1, 0, 1],
            [1, -1, 0]
        ]
        repsonses = {
            0: "**It's a tie!**",
            1: "**You win!**",
            -1: "**I win!**"
        }
        me = random.randint(0, 2)
        message = repsonses[key[me][answer]]
        thing = f"You chose: {game[answer]}\nI chose: {game[me]}.\n{message}"
        if message == repsonses[1]:
            button.style = discord.ButtonStyle.green
            self.embed.color = discord.Color.green()
        elif message == repsonses[-1]:
            button.style = discord.ButtonStyle.danger
            self.embed.color = discord.Color.red()
        for i in self.children:
            i.disabled = True
        self.embed.description = thing
        await interaction.response.edit_message(embed=self.embed, view=self)
        await self.stop()

    @discord.ui.button(label='Rock', emoji='\U0001faa8', style=discord.ButtonStyle.secondary, row=1)
    async def game_rock(self, button: discord.Button, interaction: discord.Interaction):
        await self.answer(button, interaction, 0)
        button.style = discord.ButtonStyle.success

    @discord.ui.button(label='Paper', emoji='\U0001f4f0', style=discord.ButtonStyle.secondary, row=1)
    async def game_paper(self, button: discord.Button, interaction: discord.Interaction):
        await self.answer(button, interaction, 1)
        button.style = discord.ButtonStyle.success

    @discord.ui.button(label='Scissors', emoji='\U00002702\U0000fe0f', style=discord.ButtonStyle.secondary, row=1)
    async def game_scissors(self, button: discord.Button, interaction: discord.Interaction):
        await self.answer(button, interaction, 2)
        button.style = discord.ButtonStyle.success


class CookieView(discord.ui.View):
    def __init__(self, timeout, ctx):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.winner = None

    async def on_timeout(self):
        await self.message.edit(embed=None, content='Nobody got the cookie', view=None)

    @discord.ui.button(emoji='🍪')
    async def cookie(self, button, interaction):
        self.winner = interaction.user
        button.disabled = True
        self.stop()


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
        aliases=["aki"],
        brief="Play a game of akinator.")
    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def fun_akinator(self, ctx: AvimetryContext, *, flags: AkinatorFlags):
        fm = await ctx.send("Starting game, please wait...")
        akiclient = Akinator()
        async with ctx.channel.typing():
            game = await akiclient.start_game(language=flags.mode, child_mode=flags.child)
            if akiclient.child_mode is False and ctx.channel.nsfw is False:
                return await ctx.send('Child mode can only be disabled in NSFW channels.')
            embed = discord.Embed(title='Akinator', description=f'{akiclient.step+1}. {game}')
        view = AkinatorGameView(ctx=ctx, akiclient=akiclient, member=ctx.author, embed=embed)
        await fm.delete()
        view.message = await ctx.send(embed=embed, view=view)

    @core.command(aliases=["rps"])
    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.cooldown(2, 5, commands.BucketType.member)
    async def rockpaperscissors(self, ctx: AvimetryContext, person: discord.Member):
        embed = discord.Embed(title='Rock Paper Scissors', description='Who will win?')
        view = RockPaperScissorGame(timeout=20, ctx=ctx, member=ctx.author, embed=embed, player=person)
        view.message = await ctx.send(embed=embed, view=view)

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
