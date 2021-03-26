import discord
from discord.ext import commands
import datetime
import re
from config import tokens


class AvimetryContext(commands.Context):
    @property
    def cache(self):
        return self.bot.temp

    @property
    def clean_prefix(self):
        prefix = re.sub(
            f"<@!?{self.bot.user.id}>", f"@{self.me.display_name}", self.prefix
        )
        if prefix.endswith("  "):
            prefix = f"{prefix.strip()} "
        return prefix

    async def send_raw(self, *args, **kwargs):
        return await super().send(*args, **kwargs)

    async def send(self, content=None, embed: discord.Embed = None, *args, **kwargs):
        if content:
            for key, token in tokens.items():
                if token in content:
                    content = str(content.replace(token, f"[{key} omitted. Nice try]"))
            embed = discord.Embed(description=content)
            try:
                if self.command.name == "jishaku":
                    content = None
                elif "jishaku" in self.command.qualified_name:
                    return await self.reply(content=content)
                else:
                    content = None
            except Exception:
                pass
        if discord.Embed:
            try:
                if not embed.footer:
                    embed.set_footer(
                        icon_url=str(self.author.avatar_url),
                        text=f"Requested by {self.author}",
                    )
                    embed.timestamp = datetime.datetime.utcnow()
                if not embed.color:
                    embed.color = self.author.color
                    if self.author.color == discord.Color(0):
                        embed.color = discord.Color(0x2F3136)
            except Exception:
                pass
        try:
            return await self.reply(
                content, embed=embed, *args, **kwargs, mention_author=False
            )
        except Exception:
            return await super().send(content, embed=embed, *args, **kwargs)
