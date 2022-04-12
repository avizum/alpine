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
import core
from core import Context, Bot


class HighlightCommands(core.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @core.group()
    async def highlight(self, ctx: Context):
        await ctx.send_help(ctx.command)

    @highlight.command(name="add", aliases=["a", "+"])
    async def highlight_add(self, ctx: Context, *, trigger: str):
        """
        Adds a word to your highlight list.
        """
        highlights = self.bot.cache.highlights.get(ctx.author.id)
        if highlights and trigger in [entry["phrase"] for entry in highlights]:
            return await ctx.send("This highlight is already saved.")

        query = (
            "INSERT INTO highlight (user_id, phrase) "
            "VALUES ($1, $2) "
            "RETURNING *"
        )
        data = await self.bot.pool.fetchrow(query, ctx.author.id, trigger)

        if highlights:
            highlights.append(dict(data))
        else:
            self.bot.cache.highlights[ctx.author.id] = [dict(data)]

        return await ctx.send("Highlight trigger added.")


    @highlight.command(name="remove", aliases=["r", "-"])
    async def highlight_remove(self, ctx: Context, *, trigger: str):
        """
        Removes a word from your highlight list.
        """
        highlights = self.bot.cache.highlights.get(ctx.author.id)
        if highlights and trigger not in [entry["phrase"] for entry in highlights]:
            return await ctx.send("This highlight is not saved.")

        query = (
            "DELETE FROM highlight "
            "WHERE user_id = $1 AND phrase = $2 "
            "RETURNING *"
        )
        data = await self.bot.pool.fetchrow(query, ctx.author.id, trigger)

        self.bot.cache.highlights[ctx.author.id].remove(dict(data))

        return await ctx.send("Highlight trigger removed.")
