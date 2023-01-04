"""
[Avimetry Bot]
Copyright (C) 2021 - 2023 avizum

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

import datetime

import discord
from discord import app_commands

import core
from core import Context, Bot


class HighlightCommands(core.Cog):
    """
    Notifications for words or phrases.
    """

    def __init__(self, bot: Bot) -> None:
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.emoji = "\U0001f58b"
        self.bot = bot


    @core.group(hybrid=True, invoke_without_command=True)
    async def highlight(self, ctx: Context):
        """
        Base command for highlight.
        """
        await ctx.send_help(ctx.command)

    @highlight.command(name="add", aliases=["a", "+"])
    @core.describe(trigger="The word or phrase to add.")
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
        to_add = highlights["triggers"] if highlights else [trigger]
        data = await self.bot.pool.fetchrow(query, ctx.author.id, to_add)

        if not highlights and data is not None:
            new_data = dict(data)
            new_data.pop("user_id")
            ctx.bot.cache.highlights[ctx.author.id] = new_data

        return await ctx.send("Highlight trigger added.", ephemeral=True, delete_after=10)

    @highlight.command(name="remove", aliases=["r", "-"])
    @core.describe(trigger="The word or phrase to remove.")
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

        return await ctx.send("Highlight trigger removed.", ephemeral=True, delete_after=10)

    @highlight_remove.autocomplete("trigger")
    async def highlight_remove_autocomplete(self, itn: discord.Interaction, item: str) -> list[app_commands.Choice]:
        highlights = self.bot.cache.highlights.get(itn.user.id)
        if not highlights:
            return []
        elif not item:
            return [app_commands.Choice(name=hl, value=hl) for hl in highlights["triggers"][:25]]
        return [app_commands.Choice(name=hl, value=hl) for hl in highlights["triggers"][:25] if item in hl and len(item) > 2]

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
            color=0x30C5FF,
        )

        return await ctx.send(embed=embed, delete_after=10)

    @highlight.command(name="clear", aliases=["clr"])
    async def highlight_clear(self, ctx: Context):
        """
        Removes all of your highlight triggers and blocked list.
        """
        await ctx.message.delete(delay=10)
        highlights = self.bot.cache.highlights.get(ctx.author.id)
        if not highlights:
            return await ctx.send("You don't have any highlights.")

        query = (
            "DELETE FROM highlights "
            "WHERE user_id = $1"
        )

        await self.bot.pool.execute(query, ctx.author.id)
        del self.bot.cache.highlights[ctx.author.id]
        await ctx.send("Your highlights have been cleared.", ephemeral=True, delete_after=10)

    @highlight.command(name="block", aliases=["bl"])
    @core.describe(user="The user to block from triggering highlights.")
    async def highlight_block(self, ctx: Context, *, user: discord.User):
        """
        Blocks a member from highlighting you.
        """
        await ctx.message.delete(delay=10)
        highlights = self.bot.cache.highlights.get(ctx.author.id)
        if highlights and user in highlights["blocked"]:
            return await ctx.send("This user is already blocked.")
        if highlights:
            highlights["blocked"].append(user.id)

        query = (
            "INSERT INTO highlights (user_id, blocked) "
            "VALUES ($1, $2) "
            "ON CONFLICT (user_id) DO "
            "UPDATE SET blocked = $2"
            "RETURNING *"
        )

        to_add = highlights["blocked"] if highlights else [user.id]
        data = await self.bot.pool.fetchrow(query, ctx.author.id, to_add)

        if not highlights and data is not None:
            new_data = dict(data)
            new_data.pop("user_id")
            ctx.bot.cache.highlights[ctx.author.id] = new_data

        return await ctx.send("Block list updated.", ephemeral=True, delete_after=10)

    @highlight.command(name="unblock", aliases=["unbl"])
    @core.describe(user="The user to unblock from triggering highlights.")
    async def highlight_unblock(self, ctx: Context, *, user: discord.User):
        """
        Unblocks a member from highlighting you.
        """
        await ctx.message.delete(delay=10)
        highlights = self.bot.cache.highlights.get(ctx.author.id)
        if highlights and user not in highlights["blocked"]:
            return await ctx.send("This user is not blocked.")
        if not highlights:
            return await ctx.send("You don't have a user/channel blocked.")
        highlights["blocked"].remove(user.id)

        query = (
            "UPDATE highlights "
            "SET blocked = $2 "
            "WHERE user_id = $1 "
        )

        await self.bot.pool.execute(query, ctx.author.id, highlights["blocked"])

        return await ctx.send("Block list updated.", ephemeral=True, delete_after=10)
