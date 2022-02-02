import discord
import core
import re


from utils import AvimetryBot
from typing import Optional, Union
from discord import Emoji, PartialEmoji


class ButtonRoleManager(discord.ui.View):
    """
    View that handles the buttons.

    A new view is created for each channel.
    """

    def __init__(self, channel_id):
        self.channel_id = channel_id
        super().__init__(timeout=None)


class RoleButton(discord.ui.Button[ButtonRoleManager]):
    """
    Button for button roles.

    This button handles giving the role, and removing the role from the user.
    """

    def __init__(
        self,
        *,
        role_id: int, 
        channel_id: int,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        **kwargs
    ):
        custom_id = f"role:{role_id}|channel:{channel_id}"
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            emoji=emoji,
            **kwargs
        )

    async def send_error_message(self, interaction: discord.Interaction):
        return await interaction.response.send_message(
            "An error occured while trying to give your role. Please try again later.",
            ephemeral=True,
        )

    async def callback(self, interaction: discord.Interaction):
        check = re.match(r"([0-9]{18,21}):([0-9]{18,21})", self.custom_id)
        if not check:
            return await self.send_error_message(interaction)
        guild = interaction.guild
        if guild is None:
            return await self.send_error_message(interaction)
        role = guild.get_role(int(check.group(2)))
        if not role:
            return await interaction.response.send_message(
                "Role could not be found. Maybe the role was deleted?", ephemeral=True
            )
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            return await interaction.response.send_message(
                f"Removed @{role.name} from your roles.", ephemeral=True
            )
        await interaction.user.add_roles(role)
        return await interaction.response.send_message(
            f"Added @{role.name} to your roles.", ephemeral=True
        )


class ButtonRoles(core.Cog, name="Button Roles"):
    """
    Reaction roles utilizing buttons instead of reactions.
    """

    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.emoji = "\U0001f4dc"


def setup(bot: AvimetryBot):
    bot.add_cog(ButtonRoles(bot))
