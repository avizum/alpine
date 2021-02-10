import discord
from discord.ext import commands
import datetime
from pathlib import Path

class AvimetryContext(commands.Context):

    async def send_raw(self, *args, **kwargs):
        return await super().send(*args, **kwargs)

    async def send(self, content=None, **kwargs):
        try:
            return await self.reply(content, **kwargs, mention_author=False)
        except:
            return await super().send(content, **kwargs)

    async def embed(self, *args, **kwargs):
        embed = discord.Embed(**kwargs, timestamp=datetime.datetime.utcnow())
        embed.set_footer(icon_url=str(self.author.avatar_url), text=f"Requested by {self.author}")
        await self.send(embed = embed)