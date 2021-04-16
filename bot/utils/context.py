import asyncio
import discord
import datetime
import re
from config import tokens
from discord.ext import commands


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

    @property
    async def get_prefix(self):
        get_prefix = await self.cache.get_guild_settings(self.guild.id)
        if get_prefix:
            prefix = get_prefix["prefixes"]
        if not prefix:
            return "`a.`"
        return f"`{'` | `'.join(prefix)}`"

    async def send_raw(self, *args, **kwargs):
        return await super().send(*args, **kwargs)

    async def post(self, content, syntax=None):
        if syntax is None:
            syntax = "python"
        link = await self.bot.myst.post(content, syntax=syntax)
        embed = discord.Embed(
            description=f"The output from the command {self.invoked_with} is too long, so I posted it here:\n{link}"
        )
        await self.send(embed=embed)

    async def send(self, content=None, *args, **kwargs):
        embed: discord.Embed = kwargs.get("embed")
        if self.message.id in self.bot.command_cache:
            if self.message.edited_at:
                edited_message = self.bot.command_cache[self.message.id]
                if content and "embed" in kwargs:
                    kwargs.pop("embed")
                if edited_message.reactions:
                    try:
                        await edited_message.clear_reactions()
                    except Exception:
                        return
                await edited_message.edit(content=content, *args, **kwargs)
                return edited_message
        if content:
            for key, value in tokens.items():
                if value in content:
                    content = str(content.replace(value, "[token omitted]"))
            if not self.command:
                pass
            elif self.command.qualified_name == "jishaku":
                pass
            elif "jishaku" in self.command.qualified_name:
                return await self.reply(content=content)
            else:
                embed = discord.Embed(description=content)
                content = None
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
            message = await self.reply(
                content, *args, **kwargs, mention_author=False
            )
            return message
        except Exception:
            try:
                message = await super().send(content, *args, **kwargs)
                return message
            except Exception:
                pass
            return await self.post(content or embed.description, syntax="python")
        finally:
            self.bot.command_cache[self.message.id] = message

    async def confirm(
        self, message=None, embed: discord.Embed = None, confirm_message=None, *,
        timeout=60, delete_after=True
    ):
        yes_no = [self.bot.emoji_dictionary['green_tick'], self.bot.emoji_dictionary['red_tick']]
        check_message = confirm_message or f"React with {yes_no[0]} to accept, or {yes_no[1]} to deny."
        if message:
            message = f"{message}\n\n{check_message}"
            send = await self.send(message)
        elif embed:
            embed.description = f"{embed.description}\n\n{check_message}"
            send = await self.send(embed=embed)
        for emoji in yes_no:
            await send.add_reaction(emoji)

        def check(reaction, user):
            return str(reaction.emoji) in yes_no and user == self.author and reaction.message.id == send.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = False
            pass
        else:
            if str(reaction.emoji) == yes_no[0]:
                confirm = True
            if str(reaction.emoji) == yes_no[1]:
                confirm = False
        if delete_after:
            try:
                await send.delete()
            except discord.Forbidden:
                pass
        return confirm

    async def delete(self, *args, **kwargs):
        emoji = self.bot.emoji_dictionary["red_tick"]
        message = await self.send(*args, **kwargs)
        await message.add_reaction(emoji)

        def check(reaction, user):
            return str(reaction.emoji) in emoji and user == self.author and reaction.message.id == message.id

        reaction, user = await self.bot.wait_for("reaction_add", check=check)
        if str(reaction.emoji) == emoji:
            await message.delete()
