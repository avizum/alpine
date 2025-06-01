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

import discord
from discord.ui.select import BaseSelect

__all__ = ("LayoutView", "View")


class View(discord.ui.View):
    def __init__(
        self,
        *,
        member: discord.Member | discord.User | discord.Object | None = None,
        timeout: float | None = 180.0,
    ) -> None:
        self.member: discord.Member | discord.User | discord.Object | None = member
        super().__init__(timeout=timeout)

    def disable_all(self) -> None:
        for child in self.children:
            if isinstance(child, (discord.ui.Button, BaseSelect)):
                child.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.member:
            await interaction.response.send_message(f"This menu can only be used by {self.member}", ephemeral=True)
            return False
        return True


class LayoutView(discord.ui.LayoutView):
    def __init__(
        self,
        *,
        member: discord.Member | discord.User | discord.Object | None = None,
        timeout: float | None = 180.0,
    ) -> None:
        self.member: discord.Member | discord.User | discord.Object | None = member
        super().__init__(timeout=timeout)

    def disable_all(self) -> None:
        for child in self.walk_children():
            if isinstance(child, (discord.ui.Button, BaseSelect)):
                child.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.member is None:
            return True
        if interaction.user != self.member:
            await interaction.response.send_message(f"This menu can only be used by {self.member}", ephemeral=True)
            return False
        return True
