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

import random
from typing import Literal

import discord
from discord.ext import commands
from discord.ext.commands import flag
from akinator import CantGoBackAnyFurther
from akinator.async_aki import Akinator

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
    async def yes(self, interaction: discord.Interaction, button: discord.Button):
        self.embed.description = f"{self.embed.description}\n**---**\n\nNice!"
        await self.message.edit(embed=self.embed, view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.Button):
        self.embed.description = f"{self.embed.description}\n**---**\n\nAww, Maybe next time!"
        await self.message.edit(embed=self.embed, view=None)


class AkinatorButton(discord.ui.Button['AkinatorGameView']):
    def __init__(self, label: str,  answer: str, style: discord.ButtonStyle, row: int):
        self.answer = answer
        super().__init__(label=label, style=style, row=row)

    async def callback(self, interaction: discord.Interaction) -> any:
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
        self.ctx = ctx
        self.client = client
        self.member = member
        self.embed = embed
        self.ended = False
        self.cooldown = commands.CooldownMapping.from_cooldown(2, 2.5, commands.BucketType.user)

        stop = AkinatorButton(label="End Game", answer="end", style=discord.ButtonStyle.primary, row=3)
        stop.callback = self.game_stop
        buttons = [
            AkinatorButton(label="Yes", answer="0", style=discord.ButtonStyle.green, row=1),
            AkinatorButton(label="No", answer="1", style=discord.ButtonStyle.red, row=1),
            AkinatorButton(label="Unsure", answer="2", style=discord.ButtonStyle.gray, row=1),
            AkinatorButton(label="Likely", answer="3", style=discord.ButtonStyle.blurple, row=2),
            AkinatorButton(label="Unlikely", answer="4", style=discord.ButtonStyle.gray, row=2),
            AkinatorButton(label="Go Back", answer="back", style=discord.ButtonStyle.gray, row=3),
            stop,
        ]
        for button in buttons:
            self.add_item(button)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item):
        await self.ctx.send(error)
        await super().on_error(interaction, error, item)

    async def stop(self, *args, **kwargs):
        await self.client.close()
        await self.message.edit(*args, **kwargs, view=None)
        super().stop()

    async def on_timeout(self):
        self.embed.description = "Game ended due to timeout."
        await self.stop(embed=self.embed)

    async def answer(self, interaction: discord.Interaction, answer: str) -> None:
        retry = self.cooldown.update_rate_limit(self.ctx.message)
        if retry:
            return await interaction.response.send_message(content="You are clicking too fast.", ephemeral=True)
        if answer == "back":
            try:
                nxt = await self.client.back()
                self.embed.description = f"{self.client.step+1}. {nxt}"
                await interaction.response.edit_message(embed=self.embed)
            except CantGoBackAnyFurther:
                await interaction.response.send_message("You can't go back. Sorry.", ephemeral=True)
        elif self.client.progression <= 80:
            await interaction.response.defer()
            nxt = await self.client.answer(answer)
            self.embed.description = f"{self.client.step+1}. {nxt}"
            await self.message.edit(embed=self.embed)
        else:
            await interaction.response.defer()
            await self.client.win()
            client = self.client
            await client.close()
            self.embed.description = (
                f"Are you thinking of {client.first_guess['name']} ({client.first_guess['description']})?\n"
            )
            self.embed.set_image(url=client.first_guess["absolute_picture_path"])
            await self.stop()
            new_view = AkinatorConfirmView(member=self.member, message=self.message, embed=self.embed)
            await self.message.edit(view=new_view, embed=self.embed)

    async def game_stop(self, interaction: discord.Interaction):
        await self.client.win()
        self.embed.description = "Game stopped."
        await interaction.response.edit_message(embed=self.embed, view=None)
        await self.stop()


class AkinatorFlags(commands.FlagConverter):
    mode: Literal["default", "animals", "objects"] = flag(default="default", description="The mode used for Akinator.")
    child: bool = flag(default=True, description="Whether to use child mode.")


class RockPaperScissorGame(View):
    def __init__(self, timeout=8, *, ctx, member, embed):
        super().__init__(timeout=timeout, member=member)
        self.ctx = ctx
        self.embed = embed

    async def stop(self):
        for i in self.children:
            i.disabled = True
        await self.message.edit(view=self)

    async def on_timeout(self):
        await self.stop()

    async def answer(self, button, interaction, answer):
        game = {0: "**Rock**", 1: "**Paper**", 2: "**Scissors**"}
        key = [[0, 1, -1], [-1, 0, 1], [1, -1, 0]]
        repsonses = {0: "**It's a tie!**", 1: "**You win!**", -1: "**I win!**"}
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

    @discord.ui.button(label="Rock", emoji="\U0001faa8", style=discord.ButtonStyle.secondary, row=1)
    async def game_rock(self, interaction: discord.Interaction, button: discord.Button):
        await self.answer(button, interaction, 0)
        button.style = discord.ButtonStyle.success

    @discord.ui.button(label="Paper", emoji="\U0001f4f0", style=discord.ButtonStyle.secondary, row=1)
    async def game_paper(self, interaction: discord.Interaction, button: discord.Button):
        await self.answer(button, interaction, 1)
        button.style = discord.ButtonStyle.success

    @discord.ui.button(
        label="Scissors",
        emoji="\U00002702\U0000fe0f",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def game_scissors(self, interaction: discord.Interaction, button: discord.Button):
        await self.answer(button, interaction, 2)
        button.style = discord.ButtonStyle.success


class CookieView(discord.ui.View):
    def __init__(self, timeout, ctx):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.winner = None

    async def on_timeout(self):
        await self.message.edit(embed=None, content="Nobody got the cookie", view=None)

    @discord.ui.button(emoji="🍪")
    async def cookie(self, interaction: discord.Interaction, button: discord.Button):
        self.winner = interaction.user
        button.disabled = True
        self.stop()


class RPSButton(discord.ui.Button):
    def __init__(self, label: str, player_one: discord.Member, player_two: discord.Member):
        self.player_one = player_one
        self.player_two = player_two
        self.pa = None
        self.pt = None
        super().__init__(style=discord.ButtonStyle.success, label=label)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user == self.player_one and not getattr(self.player_one, "answer", None):
            await interaction.response.send_message(content="You picked {self.label}!")
            self.pa = self.label
        elif interaction.user == self.player_two and not getattr(self.player_two, "answer", None):
            await interaction.response.send_message(content="You picked {self.label}!")
            self.pt = self.label
        print(f"Player one: {self.pt}\nPlayer two: {self.pa}")
