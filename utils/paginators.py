"""
[Alpine Bot]
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

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import discord
from discord.ext.menus import PageSource
from jishaku.paginators import WrappedPaginator

from utils.view import View

if TYPE_CHECKING:
    from core.context import Context


__all__ = (
    "Paginator",
    "PaginatorEmbed",
    "WrappedPaginator",
)


class PaginatorEmbed(discord.Embed):
    def __init__(self, *, ctx: Context, **kwargs) -> None:
        super().__init__(**kwargs)
        self.color = ctx.get_color()
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        if not ctx.interaction:
            self.set_footer(text=f"Requested by: {ctx.author}", icon_url=ctx.author.display_avatar.url)


# This paginator is essentially discord.ext.menus but changed a bit so that it uses buttons instead of reactions.
# https://github.com/Rapptz/discord-ext-menus
class BasePaginator(View):
    timeout: float | int

    def __init__(
        self,
        source: PageSource,
        *,
        ctx: Context,
        timeout: float = 180.0,
        current_page: int = 0,
        delete_message_after: bool = False,
        remove_view_after: bool = False,
        disable_view_after: bool = False,
        message: discord.Message | None = None,
    ) -> None:
        self.source: PageSource = source
        self.ctx: Context = ctx
        self.disable_view_after: bool = disable_view_after
        self.remove_view_after: bool = remove_view_after
        self.delete_message_after: bool = delete_message_after
        self.current_page: int = current_page
        self.message: discord.Message | None = message
        super().__init__(timeout=timeout, member=ctx.author)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user and interaction.user.id in (
            *self.ctx.bot.owner_ids,
            self.ctx.author.id,
        ):
            return True
        embed = discord.Embed(
            title="Error",
            description=f"This menu may only be used by {self.ctx.author}, not you. Sorry!",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    async def show_page(self, interaction: discord.Interaction, page_num: int):
        page = await self.source.get_page(page_num)
        self.current_page = page_num
        kwargs = await self.get_page_kwargs(page)

        if interaction.response.is_done():
            if self.message:
                await self.message.edit(**kwargs, view=self)
        else:
            await interaction.response.edit_message(**kwargs, view=self)

    async def show_checked_page(self, interaction: discord.Interaction, page_num: int):
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                await self.show_page(interaction, page_num)
            elif max_pages > page_num >= 0:
                await self.show_page(interaction, page_num)
        except IndexError:
            pass

    async def get_page_kwargs(self, page: int) -> dict[str, Any]:
        value = await discord.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {"content": value, "embed": None}
        elif isinstance(value, discord.Embed):
            return {"embed": value, "content": None}
        else:
            return {}

    async def on_timeout(self):
        if not self.message:
            return
        if self.disable_view_after:
            self.disable_all()
            await self.message.edit(view=self)
        elif self.remove_view_after:
            await self.message.edit(view=None)
        elif self.delete_message_after:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass
        if self.ctx.interaction is None:
            await self.ctx.message.add_reaction("<:greentick:777096731438874634>")

    async def start(self) -> discord.Message:
        await self.source._prepare_once()
        page = await self.source.get_page(self.current_page)
        kwargs = await self.get_page_kwargs(page)
        self.message = await self.ctx.send(**kwargs, view=self)
        return self.message


class SkipToPageModal(discord.ui.Modal, title="Go to page"):
    to_page = discord.ui.TextInput(label="Page Number", style=discord.TextStyle.short, min_length=1, max_length=6)

    def __init__(self, timeout: float, view: Paginator):
        super().__init__(timeout=timeout)
        self.view = view

    async def send_error(self, interaction: discord.Interaction, error: str):
        return await interaction.response.send_message(error, ephemeral=True)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            if not self.to_page.value:
                raise ValueError("Page number cannot be empty.")
            page_num = int(self.to_page.value)
            max_pages = self.view.source.get_max_pages()
            await self.view.show_checked_page(interaction, int(self.to_page.value) - 1)
            if max_pages and page_num > max_pages or page_num <= 0:
                await self.send_error(
                    interaction,
                    f"Please enter a page number between 1 and {max_pages}.",
                )
        except ValueError:
            return await self.send_error(interaction, "Please enter a number.")


class Paginator(BasePaginator):
    def __init__(
        self,
        source: PageSource,
        *,
        ctx: Context,
        timeout: float = 180.0,
        current_page: int = 0,
        delete_message_after: bool = False,
        remove_view_after: bool = False,
        disable_view_after: bool = False,
        message: discord.Message | None = None,
    ) -> None:
        super().__init__(
            source,
            ctx=ctx,
            timeout=timeout,
            current_page=current_page,
            delete_message_after=delete_message_after,
            remove_view_after=remove_view_after,
            disable_view_after=disable_view_after,
            message=message,
        )
        self.clear_items()
        self.add_items()

    def add_items(self) -> None:
        if self.source.is_paginating():
            max_pages: int = self.source.get_max_pages()  # type: ignore  # can't be None while paginating
            if max_pages <= 1:
                pass
            elif max_pages > 2:
                self.add_item(self.skip_to_first)
                self.add_item(self.go_back_one)
                self.add_item(self.show_page_number)
                self.add_item(self.go_forward_one)
                self.add_item(self.skip_to_last)
            else:
                self.add_item(self.go_back_one)
                self.add_item(self.show_page_number)
                self.add_item(self.go_forward_one)
        self.add_item(self.stop_view)

    async def show_page(self, interaction: discord.Interaction, page_num: int):
        page = await self.source.get_page(page_num)
        self.current_page = page_num
        self._update(page_num)
        kwargs = await self.get_page_kwargs(page)

        if interaction.response.is_done():
            if self.message:
                await self.message.edit(**kwargs, view=self)
        else:
            await interaction.response.edit_message(**kwargs, view=self)

    def _update(self, page: int) -> None:
        self.go_forward_one.disabled = False
        self.go_back_one.disabled = False
        self.show_page_number.disabled = False
        self.skip_to_last.disabled = False
        self.skip_to_first.disabled = False

        if self.show_page_number.emoji:
            self.show_page_number.emoji = None
        current = self.current_page + 1
        most: int = self.source.get_max_pages()  # type: ignore  # can't be None while paginating
        self.show_page_number.label = f"{current}/{most}"

        self.skip_to_first.label = "1"
        self.skip_to_last.label = str(most)

        if most <= 2:
            self.show_page_number.disabled = True

        if page + 2 == most:
            self.skip_to_last.disabled = True
        if page == 1:
            self.skip_to_first.disabled = True
        if page + 1 == most:
            self.go_forward_one.disabled = True
            self.skip_to_last.disabled = True
        if page == 0:
            self.go_back_one.disabled = True
            self.skip_to_first.disabled = True

    async def on_timeout(self) -> None:
        if not self.message:
            return
        if self.disable_view_after:
            self.disable_all()
            self.stop_view.label = "Disabled"
            await self.message.edit(view=self)
        elif self.remove_view_after:
            await self.message.edit(view=None)
        elif self.delete_message_after:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass
        if self.ctx.interaction is None:
            await self.ctx.message.add_reaction("<:greentick:777096731438874634>")

    async def start(self) -> discord.Message:
        self._update(self.current_page)
        return await super().start()

    @discord.ui.button(emoji="\U000023ee\U0000fe0f")
    async def skip_to_first(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Skips to the first page.
        """
        await self.show_page(interaction, 0)

    @discord.ui.button(emoji="\U000025c0\U0000fe0f")
    async def go_back_one(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Goes back one page.
        """
        await self.show_checked_page(interaction, self.current_page - 1)

    @discord.ui.button(
        emoji="<:alpine:1020851768143380522>",
        disabled=False,
        style=discord.ButtonStyle.blurple,
    )
    async def show_page_number(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Shows the current page number.
        This button also is used for skipping to pages.
        """
        await interaction.response.send_modal(SkipToPageModal(self.timeout, self))

    @discord.ui.button(emoji="\U000025b6\U0000fe0f")
    async def go_forward_one(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Goes to the next page.
        """
        await self.show_checked_page(interaction, self.current_page + 1)

    @discord.ui.button(emoji="\U000023ed\U0000fe0f")
    async def skip_to_last(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Skips to the last page.
        """
        await self.show_page(interaction, self.source.get_max_pages() - 1)  # type: ignore # can't be None while paginating

    @discord.ui.button(emoji="\U000023f9\U0000fe0f", label="Stop", style=discord.ButtonStyle.red)
    async def stop_view(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        Stops the paginator and view.
        """
        if self.disable_view_after:
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
            button.label = "Stopped"
            await interaction.response.edit_message(view=self)
        elif self.remove_view_after:
            await interaction.response.edit_message(view=None)
        elif self.delete_message_after and self.message is not None:
            await self.message.delete()
        if self.ctx.interaction is None:
            await self.ctx.message.add_reaction("<:greentick:777096731438874634>")
        self.stop()


WrappedPaginator = WrappedPaginator
