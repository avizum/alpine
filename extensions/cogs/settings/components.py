import discord
from discord import ui

from utils.view import View


class WelcomerView(View):
    def __init__(self, config: dict, ctx):
        self.config = config
        super().__init__(ctx.author)


class ToggleButton(ui.Button):
    def __init__(self, config: dict, is_on: bool):
        self.config = config
        button_style = ui.ButtonStyle.green if is_on else ui.ButtonStyle.red
        button_text = "Enabled" if is_on else "Disabled"
        super().__init__(
            style=button_style,
            label=button_text,
        )

    async def callback(self, interaction: discord.Interaction) -> any:
        ...
