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

import discord

__all__ = ("View",)


class View(discord.ui.View):
    def __init__(self, *, member: discord.Member | discord.User, timeout: int | float = 180, **kwargs) -> None:
        self.member: discord.Member | discord.User = member
        super().__init__(timeout=timeout, **kwargs)

    def disable_all(self) -> None:
        for child in self.children:
            if isinstance(child, (discord.ui.Button, discord.ui.Select)):
                child.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.member:
            embed = discord.Embed(description=f"This can only be used by {self.member}.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True
