"""
Base View to make things easier.
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


class AvimetryView(discord.ui.View):
    def __init__(self, *, member: discord.Member, timeout: int = 180):
        self.member = member
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.member:
            embed = discord.Embed(description=f"This can only be used by {self.member}.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True
