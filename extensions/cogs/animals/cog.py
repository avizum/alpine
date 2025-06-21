"""
[Alpine Bot]
Copyright (C) 2021 - 2024 avizum

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

import datetime as dt
from io import BytesIO
from typing import TYPE_CHECKING

import discord

import core
from utils import Timer

if TYPE_CHECKING:
    from datetime import datetime

    from somerandomapi.types.animal import ValidAnimal

    from core import Bot, Context


class Animals(core.Cog):
    """
    Get images of animals.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)
        self.emoji = "\U0001f98a"

    async def do_animal(self, ctx: Context, animal: ValidAnimal) -> None:
        async with ctx.channel.typing():
            with Timer() as timer:
                ani_info = await self.bot.sr.animal.get_image_and_fact(animal)
                get_image = await self.bot.session.get(ani_info.image)
                ani_file = discord.File(BytesIO(await get_image.read()), filename=f"{animal}.png")
        embed = discord.Embed(title=f"Here is {animal}", description=f"Fun Fact: {ani_info.fact}")
        embed.set_image(url=f"attachment://{ani_file.filename}")
        embed.set_footer(
            text=f"Powered by Some Random API | Processed in {timer.total_time * 1000:,.2f}ms",
        )
        await ctx.send(file=ani_file, embed=embed, no_edit=True)

    @core.command()
    async def dog(self, ctx: Context):
        """
        Gets a random image of a dog online.
        """
        await self.do_animal(ctx, "dog")

    @core.command()
    async def cat(self, ctx: Context):
        """
        Gets a random image of a cat online.
        """
        await self.do_animal(ctx, "cat")

    @core.command()
    async def panda(self, ctx: Context):
        """
        Gets a random image of a panda online.
        """
        await self.do_animal(ctx, "panda")

    @core.command()
    async def fox(self, ctx: Context):
        """
        Gets a random image of a fox online.
        """
        await self.do_animal(ctx, "fox")

    @core.command()
    async def koala(self, ctx: Context):
        """
        Gets a random image of a koala online.
        """
        await self.do_animal(ctx, "koala")

    @core.command(aliases=["birb"])
    async def bird(self, ctx: Context):
        """
        Gets a random image of a bird online.
        """
        await self.do_animal(ctx, "bird")

    @core.command()
    async def racoon(self, ctx: Context):
        """
        Gets a random image of a racoon online.
        """
        await self.do_animal(ctx, "racoon")

    @core.command()
    async def kangaroo(self, ctx: Context):
        """
        Gets a random image of a kangaroo online.
        """
        await self.do_animal(ctx, "kangaroo")

    @core.command()
    async def duck(self, ctx: Context):
        """
        Gets a random image of a duck online.
        """
        async with self.bot.session.get("https://random-d.uk/api/v2/random") as resp:
            image = await resp.json()
        embed = discord.Embed(title="Here is a duck")
        embed.set_image(url=image["url"])
        await ctx.send(embed=embed)
