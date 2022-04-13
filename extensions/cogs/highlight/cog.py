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
import discord

import core
from core import Context, Bot


class HighlightCommands(core.Cog):
    """
    Notifications for words or phrases.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.emoji = "\U0001f58b"

    @core.group()
    async def highlight(self, ctx: Context):
        """
        Base command for highlight.
        """
        await ctx.send_help(ctx.command)

    @highlight.command(name="add", aliases=["a", "+"])
    async def highlight_add(self, ctx: Context, *, trigger: str):
        """
        Adds a word to your highlight list.
        """
        await ctx.message.delete(delay=10)
        highlights = self.bot.cache.highlights.get(ctx.author.id)
        if highlights and trigger in highlights["triggers"]:
            return await ctx.send("This is already a highlight.")
        if highlights:
            highlights["triggers"].append(trigger)

        query = (
            "INSERT INTO highlights (user_id, triggers) "
            "VALUES ($1, $2) "
            "ON CONFLICT (user_id) DO "
            "UPDATE SET triggers = $2"
            "RETURNING *"
        )

        trigger = highlights["triggers"] or [trigger]
        data = await self.bot.pool.fetchrow(query, ctx.author.id, trigger)

        if not highlights:
            new_data = dict(data)
            new_data.pop("user_id")
            ctx.bot.cache.highlights[ctx.author.id] = new_data

        return await ctx.send("Highlight trigger added.", delete_after=10)

    @highlight.command(name="remove", aliases=["r", "-"])
    async def highlight_remove(self, ctx: Context, *, trigger: str):
        """
        Removes a word from your highlight list.
        """
        await ctx.message.delete(delay=10)
        highlights = self.bot.cache.highlights.get(ctx.author.id)
        if not highlights:
            return await ctx.send("You don't have any highlights.")
        if trigger not in highlights["triggers"]:
            return await ctx.send("This highlight is not saved.")

        query = "UPDATE highlights " "SET triggers = $2 " "WHERE user_id = $1 "

        highlights["triggers"].remove(trigger)
        await self.bot.pool.execute(query, ctx.author.id, highlights["triggers"])

        return await ctx.send("Highlight trigger removed.", delete_after=10)

    @highlight.command(name="list", aliases=["l"])
    async def highlight_list(self, ctx: Context):
        """
        Lists all your highlight triggers.
        """
        await ctx.message.delete(delay=10)
        highlights = self.bot.cache.highlights.get(ctx.author.id)
        if not highlights:
            return await ctx.send("You don't have any highlights.")

        nl = "\n"
        embed = discord.Embed(
            title="Your Triggers",
            description=nl.join(highlights["triggers"]),
            color=0xF2D413,
        )

        return await ctx.send(embed=embed, delete_after=10)
