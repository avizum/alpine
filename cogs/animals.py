"""
Animal commands
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

from utils import core
from io import BytesIO
from utils.utils import Timer
from utils import AvimetryContext, AvimetryBot
from discord.ext import commands


class Animals(commands.Cog):
    def __init__(self, bot: AvimetryBot):
        """
        Get images of animals.
        """
        self.bot = bot
        self.load_time = datetime.datetime.now()

    async def do_animal(self, ctx: AvimetryContext, animal: str):
        async with ctx.channel.typing():
            with Timer() as timer:
                e = await self.bot.sr.get_image(animal)
                file = discord.File(BytesIO(await e.read()), filename=f"{animal}.png")
        embed = discord.Embed(
            title=f"Here is {animal}",
            description=f"Powered by Some Random API\nProcessed in `{timer.total_time:,.2f}ms`"
        )
        embed.set_image(url=f"attachment://{animal}.png")
        await ctx.send(file=file, embed=embed)

    @core.command()
    async def dog(self, ctx: AvimetryContext):
        """
        Gets a random image of a dog online.
        """
        await self.do_animal(ctx, "dog")

    @core.command()
    async def cat(self, ctx: AvimetryContext):
        """
        Gets a random image of a cat online.
        """
        await self.do_animal(ctx, "cat")

    @core.command()
    async def panda(self, ctx: AvimetryContext):
        """
        Gets a random image of a panda online.
        """
        await self.do_animal(ctx, "panda")

    @core.command()
    async def fox(self, ctx: AvimetryContext):
        """
        Gets a random image of a fox online.
        """
        await self.do_animal(ctx, "fox")

    @core.command()
    async def koala(self, ctx: AvimetryContext):
        """
        Gets a random image of a koala online.
        """
        await self.do_animal(ctx, "koala")

    @core.command(aliases=['birb'])
    async def bird(self, ctx: AvimetryContext):
        """
        Gets a random image of a bird online.
        """
        await self.do_animal(ctx, "birb")

    @core.command()
    async def racoon(self, ctx: AvimetryContext):
        """
        Gets a random image of a racoon online.
        """
        await self.do_animal(ctx, "racoon")

    @core.command()
    async def kangaroo(self, ctx: AvimetryContext):
        """
        Gets a random image of a kangaroo online.
        """
        await self.do_animal(ctx, "kangaroo")

    @core.command()
    async def duck(self, ctx: AvimetryContext):
        """
        Gets a random image of a duck online.
        """
        async with self.bot.session.get("https://random-d.uk/api/v2/random") as resp:
            image = await resp.json()
        embed = discord.Embed(title="Here is a duck")
        embed.set_image(url=image['url'])
        await ctx.send(embed=embed)


def setup(bot: AvimetryBot):
    bot.add_cog(Animals(bot))
