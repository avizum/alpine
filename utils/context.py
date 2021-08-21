"""
Subclassed Command context
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

import asyncio
import discord
import datetime
import re

from .avimetry import AvimetryBot
from discord.ext import commands

emoji_regex = '<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>'


class TrashView(discord.ui.View):
    def __init__(self, timeout, ctx):
        super().__init__(timeout=timeout)
        self.ctx = ctx

    async def interaction_check(self, interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message('no', ephemeral=True)
        return True

    @discord.ui.button(emoji='<:redtick:777096756865269760>', style=discord.ButtonStyle.danger)
    async def trash(self, button, interaction):
        await self.message.delete()


class ConfirmView(discord.ui.View):
    def __init__(self, timeout: int, ctx: "AvimetryContext"):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.value = None

    async def stop(self):
        for button in self.children:
            button.disabled = True
        await self.message.edit(view=self)
        super().stop()

    async def interaction_check(self, interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message(
                f"This confirm menu belongs to {self.ctx.author.mention}, not you.",
                ephemeral=True
            )
        return True

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes(self, button, interaction):
        self.value = True
        await self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no(self, button, interaction):
        self.value = False
        await self.stop()


class ConfirmResult:
    def __init__(self, message: discord.Message, result: bool):
        self.message = message
        self.result = result

    def __repr__(self):
        return f"<ConfirmResult result={self.result}>"


class AvimetryContext(commands.Context):
    def __init__(self, *, bot: AvimetryBot, **kwargs):
        super().__init__(bot=bot, **kwargs)
        self.tokens = []
        self.tokens.extend(self.bot.settings['bot_tokens'].values())
        self.tokens.extend(self.bot.settings['api_tokens'].values())
        self.tokens.extend(self.bot.settings['webhooks'].values())

    @property
    def cache(self):
        return self.bot.cache

    @property
    def pool(self):
        return self.bot.pool

    @property
    def clean_prefix(self):
        match = re.match(emoji_regex, self.prefix)
        if match:
            return re.sub(emoji_regex, match.group(2), self.prefix)

        return re.sub(
            f"<@!?{self.bot.user.id}>", f"@{self.me.display_name} ", self.prefix
        )

    @property
    def content(self):
        return self.message.content

    @property
    async def get_prefix(self):
        get_prefix = await self.cache.get_guild_settings(self.guild.id)
        if get_prefix:
            prefix = get_prefix["prefixes"]
        if not prefix:
            return "`a.`"
        return f"`{'` | `'.join(prefix)}`"

    async def no_reply(self, *args, **kwargs):
        return await super().send(*args, **kwargs)

    async def post(self, content, syntax=None, gist: bool = False):
        if gist:
            raise NotImplementedError("Will add later")
        if syntax is None:
            syntax = "python"
        link = await self.bot.myst.post(content, syntax=syntax)
        embed = discord.Embed(
            description=f"Output for {self.command.qualified_name}: [Here]({link})"
        )
        await self.send(embed=embed)

    async def determine_color(self):
        base = self.author.color
        data = self.cache.users.get(self.author.id)
        try:
            color = data.get('color')
            if not color:
                color = base
        except AttributeError:
            color = self.author.color
        if color == discord.Color(0):
            if await self.bot.is_owner(self.author):
                color = discord.Color(0x01b9c0)
            else:
                color = discord.Color(0x2F3136)
        return color

    async def send(self, content: str = None, embed: discord.Embed = None, no_reply: bool = False, **kwargs):
        if content:
            content = str(content)
            for token in self.tokens:
                content = content.replace(token, "[config omitted]")
        if embed:
            if not embed.footer:
                embed.set_footer(
                    text=f"Requested by {self.author}",
                    icon_url=str(self.author.avatar.url)
                )
                embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            if not embed.color:
                embed.color = await self.determine_color()
        if self.message.id in self.bot.command_cache and self.message.edited_at:
            message = self.bot.command_cache[self.message.id]
            try:
                await message.edit(content=content, embed=embed, **kwargs)
            except Exception:
                self.message._edited_timestamp = None
                self.send(content=content, embed=embed, mention_author=False, **kwargs)
        elif no_reply:
            message = await super().send(content=content, embed=embed, mention_author=False, **kwargs)
        else:
            message = await self.reply(content=content, embed=embed, mention_author=False, **kwargs)

        self.bot.command_cache[self.message.id] = message
        return message

    def codeblock(self, content: str, language: str = 'py'):
        return f"```{language}\n{content}\n```"

    async def confirm(
        self, message=None, embed: discord.Embed = None, confirm_message=None, *,
        timeout=60, delete_after=False, no_reply=False, remove_view_after=False
    ):

        view = ConfirmView(timeout=timeout, ctx=self)
        check_message = confirm_message or 'Press "yes" to accept, or press "no" to deny.'
        if no_reply is True:
            send = await self.no_reply(content=message, embed=embed, view=view)
        elif message:
            message = f"{message}\n\n{check_message}"
            send = await self.send(message, view=view)
        elif embed:
            embed.description = f"{embed.description}\n\n{check_message}"
            send = await self.send(embed=embed, view=view)
        view.message = send
        await view.wait()
        if delete_after:
            await send.delete()
        if remove_view_after:
            await view.message.edit(view=None)
        return ConfirmResult(send, view.value)

    async def prompt(
        self, message=None, embed: discord.Embed = None, *,
        timeout=60, delete_after=True, raw=False
    ):
        if raw is True:
            send = await self.no_reply(content=message, embed=embed)
        elif message:
            message = f"{message}"
            send = await self.send(message)
        elif embed:
            embed.description = f"{embed.description}\n\n{message or ''}"
            send = await self.send(embed=embed)

        def check(message: discord.Message):
            return self.author == message.author and self.channel == message.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = False
            pass
        else:
            return msg.content
        if delete_after:
            await send.delete()
        return confirm

    async def can_delete(self, *args, **kwargs):
        view = TrashView(timeout=None, ctx=self)
        view.message = await self.send(*args, **kwargs, view=view)


def setup(bot):
    bot.context = AvimetryContext


def teardown(bot):
    bot.context = commands.Context
