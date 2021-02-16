import discord
from discord.ext import commands
import datetime
from pathlib import Path

class AvimetryContext(commands.Context):
    async def send_raw(self, *args, **kwargs):
        return await super().send(*args, **kwargs)

    async def send(self, content=None, embed: discord.Embed=None, *args, **kwargs):
        if self.command.qualified_name in ["jishaku shell", "jishaku cat", "jishaku source", "jishaku rtt"]:
            return await super().send(content=content)

        if content:
            embed=discord.Embed(description=content)
            content=None
        if discord.Embed:
            try:
                if not embed.footer:
                    embed.set_footer(icon_url=str(self.author.avatar_url), text=f"Invoked by {self.author}")
                if not embed.color:
                    embed.color=self.author.color
                embed.timestamp=datetime.datetime.utcnow()
            except:
                pass

        try:
            return await self.reply(content, embed=embed, *args, **kwargs, mention_author=False)
        except:
            return await super().send(content, embed=embed, *args, **kwargs)

    async def embed(self, *args, **kwargs):
        embed = discord.Embed(**kwargs, timestamp=datetime.datetime.utcnow())
        embed.set_footer(icon_url=str(self.author.avatar_url), text=f"Requested by {self.author}")
        await self.send(embed = embed)