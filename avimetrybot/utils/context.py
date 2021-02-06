import discord
from discord.ext import commands
import datetime
from pathlib import Path


class AvimetryContext(commands.Context):

    async def embed(self, *args, **kwargs):
        """Sends an embed with the args given"""
        embed = discord.Embed(**kwargs, timestamp=datetime.datetime.utcnow())
        embed.set_footer(icon_url=str(self.author.avatar_url), text=f"Requested by {self.author}")
        return await super().send(embed = embed)

    async def send(self, content=None, **kwargs):
        try:
            return await self.reply(content, **kwargs, mention_author=True)
        except:
            return await super().send(content, **kwargs)


            