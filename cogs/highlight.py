import discord
import re

from discord.ext import commands
from utils import AvimetryBot


class Highlight(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot:
            return
        words = "avi|asd|lol|stupid"
        match = re.findall(rf"({words}\s*)", message.content, flags=re.IGNORECASE)
        if match:
            match_embed = discord.Embed(
                title="Highlight detected",
                description=f"In {message.channel.mention}, you were highlighted with the word(s) `{', '.join(match)}`"
            )
            match_embed.add_field(name="Message content:", value=message.content)
            await message.channel.send(embed=match_embed)
        return


def setup(avi: AvimetryBot):
    avi.add_cog(Highlight(avi))
