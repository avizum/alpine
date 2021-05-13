"""
Currency system for the bot
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
from utils import AvimetryContext, AvimetryBot
from discord.ext import commands


AVICOIN = "◎"


class Currency(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    @commands.command(
        aliases=["bal"],
        enabled=False
    )
    async def balance(self, ctx: AvimetryContext):
        bal_embed = discord.Embed(
            title=f"{ctx.author.name}'s Balance",
            description=f"{AVICOIN} 0"
        )
        await ctx.send(embed=bal_embed)


def setup(avi):
    pass  # avi.add_cog(Currency(avi))
