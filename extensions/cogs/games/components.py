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

import random

import discord
from asyncakinator import Akinator, Answer, CantGoBackAnyFurther, InvalidLanguage, InvalidTheme, Language, Theme
from discord.ext import commands
from discord.ext.commands import flag

from core import Context
from utils import View


class AkinatorConfirmView(View):
    def __init__(
        self,
        *,
        member: discord.Member,
        timeout: int = 60,
        message: discord.Message,
        embed: discord.Embed,
    ):
        super().__init__(member=member, timeout=timeout)
        self.message = message
        self.embed = embed

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed.description = f"{self.embed.description}\n**---**\n\nNice!"
        await self.message.edit(embed=self.embed, view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.embed.description = f"{self.embed.description}\n**---**\n\nAww, Maybe next time!"
        await self.message.edit(embed=self.embed, view=None)


class AkinatorButton(discord.ui.Button["AkinatorGameView"]):
    def __init__(self, label: str, answer: Answer | str, style: discord.ButtonStyle, row: int):
        self.answer = answer
        super().__init__(label=label, style=style, row=row)

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        await self.view.answer(interaction, self.answer)


class AkinatorGameView(View):
    def __init__(
        self,
        *,
        member: discord.Member,
        ctx: Context,
        client: Akinator,
        embed: discord.Embed,
    ):
        super().__init__(member=member)
        self.ctx: Context = ctx
        self.client: Akinator = client
        self.member: discord.Member = member
        self.message: discord.Message | None = None
        self.embed: discord.Embed = embed
        self.ended: bool = False
        self.cooldown: commands.CooldownMapping = commands.CooldownMapping.from_cooldown(2, 2.5, commands.BucketType.user)

        stop = AkinatorButton(label="End Game", answer="end", style=discord.ButtonStyle.primary, row=3)
        stop.callback = self.game_stop
        buttons = [
            AkinatorButton(label="Yes", answer=Answer.YES, style=discord.ButtonStyle.green, row=1),
            AkinatorButton(label="No", answer=Answer.NO, style=discord.ButtonStyle.red, row=1),
            AkinatorButton(label="Unsure", answer=Answer.I_DONT_KNOW, style=discord.ButtonStyle.gray, row=1),
            AkinatorButton(label="Likely", answer=Answer.PROBABLY, style=discord.ButtonStyle.blurple, row=2),
            AkinatorButton(label="Unlikely", answer=Answer.PROBABLY_NOT, style=discord.ButtonStyle.gray, row=2),
            AkinatorButton(label="Go Back", answer=Answer.BACK, style=discord.ButtonStyle.gray, row=3),
            stop,
        ]
        for button in buttons:
            self.add_item(button)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        await self.ctx.send(str(error))
        await super().on_error(interaction, error, item)

    async def stop(self, *args, **kwargs):
        await self.client.close()
        if self.message is not None:
            await self.message.edit(*args, **kwargs, view=None)
        super().stop()

    async def on_timeout(self):
        self.embed.description = "Game ended due to timeout."
        await self.stop(embed=self.embed)

    async def answer(self, interaction: discord.Interaction, answer: Answer | str) -> None:
        if self.message is None:
            return
        retry = self.cooldown.update_rate_limit(self.ctx.message)
        if retry:
            return await interaction.response.send_message(content="You are clicking too fast.", ephemeral=True)
        if self.client.progression <= 80:
            assert isinstance(answer, Answer)
            await interaction.response.defer()
            try:
                nxt = await self.client.answer(answer)
            except CantGoBackAnyFurther:
                return await interaction.followup.send("You can't go back. Sorry.", ephemeral=True)
            self.embed.description = f"{self.client.step+1}. {nxt}"
            await self.message.edit(embed=self.embed)
        else:
            await interaction.response.defer()
            await self.client.win()
            client = self.client
            await client.close()
            self.embed.description = f"Are you thinking of {client.first_guess.name} ({client.first_guess.description})?\n"
            self.embed.set_image(url=client.first_guess.absolute_picture_path)
            await self.stop()
            new_view = AkinatorConfirmView(member=self.member, message=self.message, embed=self.embed)
            await self.message.edit(view=new_view, embed=self.embed)

    async def game_stop(self, interaction: discord.Interaction):
        await self.client.win()
        self.embed.description = "Game stopped."
        await interaction.response.edit_message(embed=self.embed, view=None)
        await self.stop()


class LanguageConverter(str, commands.Converter):
    async def convert(self, ctx: Context, argument: str) -> Language:
        try:
            return Language.from_str(argument)
        except InvalidLanguage as e:
            raise commands.BadArgument("Invalid language provided.") from e


class ThemeConverter(str, commands.Converter):
    async def convert(self, ctx: Context, argument: str) -> Theme:
        try:
            return Theme.from_str(argument)
        except InvalidTheme as e:
            raise commands.BadArgument("Invalid language provided.") from e


class AkinatorFlags(commands.FlagConverter):
    language: Language = flag(default=Language.ENGLISH, converter=LanguageConverter, description="The language to use.")
    theme: Theme = flag(default=Theme.CHARACTERS, converter=ThemeConverter, description="The theme to use.")
    child: bool = flag(default=True, description="Whether to use child mode.")


class CookieView(discord.ui.View):
    def __init__(self, timeout: int, ctx: Context) -> None:
        super().__init__(timeout=timeout)
        self.ctx: Context = ctx
        self.winner: discord.Member | discord.User | None = None
        self.message: discord.Message | None = None

    async def on_timeout(self) -> None:
        if self.message is not None:
            await self.message.edit(embed=None, content="Nobody got the cookie", view=None)

    @discord.ui.button(emoji="🍪")
    async def cookie(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.winner = interaction.user
        button.disabled = True
        self.stop()


class RPSButton(discord.ui.Button["RPSView"]):
    def __init__(self, emoji: str, label: str, answer: int) -> None:
        self.answer: int = answer
        super().__init__(style=discord.ButtonStyle.secondary, label=label, emoji=emoji)

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        self.style = discord.ButtonStyle.blurple
        if interaction.user == self.view.player:
            if self.view.player_one_response is None:
                self.view.player_one_response = self.answer
                self.view.player_one_str_response = self.label
                await interaction.response.send_message(f"You chose {self.label}", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"You already chose {self.view.player_one_str_response}", ephemeral=True
                )
        if interaction.user == self.view.opponent:
            if self.view.player_two_response is None:
                self.view.player_two_response = self.answer
                self.view.player_two_str_response = self.label
                await interaction.response.send_message(f"You chose {self.label}", ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"You already chose {self.view.player_two_str_response}", ephemeral=True
                )
        if self.view.player_one_response is None or self.view.player_two_response is None:
            return
        return await self.view.determine_winner()


class RPSView(View):
    children: list[RPSButton]
    player_one_response: int | None = None
    player_one_str_response: str | None = None
    player_two_response: int | None = None
    player_two_str_response: str | None = None

    def __init__(self, embed: discord.Embed, context: Context, opponent: discord.Member) -> None:
        super().__init__(member=context.author, timeout=60)
        self.message: discord.Message
        self.embed: discord.Embed = embed
        self.player: discord.Member = context.author
        self.opponent: discord.Member = opponent

        if self.opponent == context.me:
            self.player_two_response = random.randint(0, 2)

        for emoji, label, value in [
            ("\U0001faa8", "Rock", 0),
            ("\U0001f4f0", "Paper", 1),
            ("\U00002702\U0000fe0f", "Scissors", 2),
        ]:
            self.add_item(RPSButton(emoji=emoji, label=label, answer=value))

    async def on_timeout(self) -> None:
        self.embed.description = "Game ended due to timeout."
        await self.message.edit(embed=self.embed, view=None)
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user in (self.player, self.opponent)

    async def determine_winner(self) -> None:
        if self.player_one_response is None or self.player_two_response is None:
            return
        game: dict[int, str] = {0: "**Rock**", 1: "**Paper**", 2: "**Scissors**"}
        key: list[list[int]] = [[0, 1, -1], [-1, 0, 1], [1, -1, 0]]
        repsonses: dict[int, str] = {0: "**It's a tie!**", 1: f"**{self.player} wins!**", -1: f"**{self.opponent} wins!**"}

        message = repsonses[key[self.player_two_response][self.player_one_response]]
        thing = (
            f"{self.player.mention} chose: {game[self.player_one_response]}\n"
            f"{self.opponent.mention} chose: {game[self.player_two_response]}.\n"
            f"{message}"
        )

        self.embed.description = thing
        self.disable_all()
        await self.message.edit(embed=self.embed, view=self)
        self.stop()
