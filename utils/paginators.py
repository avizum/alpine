"""
Paginators for commands.
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

from discord.ext import menus
from discord.ext.menus import button, Position


class AvimetryPages(menus.MenuPages):
    def __init__(self, source, **kwargs):
        super().__init__(source, clear_reactions_after=True, **kwargs)

    async def send_initial_message(self, ctx, channel):
        page = await self._source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        return await ctx.send(**kwargs)

    async def update(self, payload):
        if self._can_remove_reactions:
            if payload.event_type == 'REACTION_ADD':
                await self.bot.http.remove_reaction(
                    payload.channel_id, payload.message_id,
                    payload.emoji, payload.member.id
                )
            elif payload.event_type == 'REACTION_REMOVE':
                return
        await super().update(payload)

    def _skip_double_triangle_buttons(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 2

    @button('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f', position=Position(0),
            skip_if=_skip_double_triangle_buttons)
    async def go_to_first_page(self, payload):
        """go to the first page"""
        await self.show_page(0)

    @button('\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f', position=Position(1))
    async def go_to_previous_page(self, payload):
        """go to the previous page"""
        await self.show_checked_page(self.current_page - 1)

    @button('\N{BLACK SQUARE FOR STOP}\ufe0f', position=Position(2))
    async def stop_pages(self, payload):
        """stops the pagination session."""
        self.stop()

    @button('\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f', position=Position(3))
    async def go_to_next_page(self, payload):
        """go to the next page"""
        await self.show_checked_page(self.current_page + 1)

    @button('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f', position=Position(4),
            skip_if=_skip_double_triangle_buttons)
    async def go_to_last_page(self, payload):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        await self.show_page(self._source.get_max_pages() - 1)
