"""
[Avimetry Bot]
Copyright (C) 2021 - 2022 avizum

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

from __future__ import annotations

import datetime
import re
from typing import Sequence, TYPE_CHECKING

import discord
from asyncgist import File
from discord.ext import commands, menus
from discord.utils import MISSING

from utils.view import View
from utils.emojis import Emojis
from utils.paginators import Paginator, WrappedPaginator

if TYPE_CHECKING:
    from .avimetry import Bot
    from discord import (
        Embed,
        GuildSticker,
        StickerItem,
        AllowedMentions,
        Message,
        MessageReference,
        PartialMessage,
    )


emoji_regex = "<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>"


class TrashView(View):
    def __init__(self, *, member: discord.Member, timeout: int = 60, ctx: Context) -> None:
        self.ctx = ctx
        super().__init__(member=member, timeout=timeout)

    async def stop(self) -> None:
        for button in self.children:
            button.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.NotFound:
            pass
        super().stop()

    async def on_timeout(self) -> None:
        await self.stop()

    @discord.ui.button(emoji="\U0001f5d1", style=discord.ButtonStyle.danger)
    async def trash(self, interaction: discord.Interaction, button: discord.Button):
        await self.message.delete()
        await self.ctx.message.add_reaction(Emojis.GREEN_TICK)


class ConfirmView(View):
    def __init__(self, *, member: discord.Member, timeout=None):
        super().__init__(member=member, timeout=timeout)
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.Button):
        self.value = False
        self.stop()


class ConfirmResult:
    def __init__(self, message: discord.Message, result: bool):
        self.message = message
        self.result = result

    def __repr__(self):
        return f"<ConfirmResult result={self.result}>"


class AutoPageSource(menus.ListPageSource):
    def __init__(self, entry: str | list, language: str = "", *, limit: int = 1000):
        if isinstance(entry, list):
            entry = entry
        elif isinstance(entry, str):
            pag = WrappedPaginator(prefix=f"```{language}", suffix="```", max_size=limit, force_wrap=True)
            pag.add_line(entry)
            entry = pag.pages
        elif isinstance(entry, commands.Paginator):
            entry = entry.pages
        super().__init__(entry, per_page=1)

    async def format_page(self, menu, page):
        return page


class Context(commands.Context):
    def __init__(self, *, bot: Bot, **kwargs) -> None:
        super().__init__(bot=bot, **kwargs)
        self.bot: Bot = bot
        self.locally_handled: bool = False
        if self.interaction:
            self.message.content = f"/{self.invoked_with}"
        tokens: list[str] = []
        tokens.extend(self.bot.settings["bot_tokens"].values())
        tokens.extend(self.bot.settings["api_tokens"].values())
        tokens.extend(self.bot.settings["webhooks"].values())
        self.tokens: list[str] = tokens

    @property
    def cache(self):
        return self.bot.cache

    @property
    def pool(self):
        return self.bot.pool

    @property
    def clean_prefix(self) -> str:
        match = re.match(emoji_regex, self.prefix)
        if match:
            return re.sub(emoji_regex, match.group(2), self.prefix)

        return re.sub(f"<@!?{self.bot.user.id}>", f"@{self.me.display_name} ", self.prefix)

    @property
    def content(self) -> str:
        return self.message.content

    @property
    async def get_prefix(self) -> str:
        get_prefix = await self.cache.get_guild_settings(self.guild.id)
        if get_prefix:
            prefix = get_prefix["prefixes"]
        if not prefix:
            return "`a.`"
        return f"`{'` | `'.join(prefix)}`"

    @property
    def reference(self) -> Message | None:
        ref = self.message.reference
        if isinstance(ref.resolved, discord.Message):
            return ref.resolved
        return None

    async def no_reply(self, *args, **kwargs) -> Message | None:
        return await super().send(*args, **kwargs)

    async def post(self, content, syntax: str = "py", gist: bool = False) -> Message | None:
        if gist:
            gist_file = [File(filename=f"output.{syntax}", content=content)]
            link = (await self.bot.gist.post_gist(description=str(self.author), files=gist_file, public=True)).html_url
        else:
            link = await self.bot.myst.post(content, syntax=syntax)
        embed = discord.Embed(description=f"Output for {self.command.qualified_name}: [Here]({link})")
        await self.send(embed=embed)

    async def fetch_color(self, member: discord.Member | None = None) -> discord.Color:
        member = member or self.author
        data = self.cache.users.get(member.id)
        color = data.get("color") if data else None
        if not color:
            color = member.color
        if color == discord.Color(0):
            color = discord.Color(0x2F3136)
            if await self.bot.is_owner(member):
                color = discord.Color(0x01B9C0)
        return color

    def get_color(self, member: discord.Member | None = None) -> discord.Color:
        member = member or self.author
        data = self.cache.users.get(member.id)
        color = data.get("color") if data else None
        if not color:
            color = member.color
        elif color == discord.Color(0):
            color = 0x2F3136
        return color

    async def paginate(
        self,
        entry: str | list[Embed],
        lang: str | None = None,
        *,
        limit: int = 1000,
        delete_message_after: bool = True,
        remove_view_after: bool = False,
        disable_view_after: bool = False,
    ) -> Message | None:
        lang = lang or ""
        menu = Paginator(
            AutoPageSource(entry, lang, limit=limit),
            ctx=self,
            remove_view_after=remove_view_after,
            delete_message_after=delete_message_after,
            disable_view_after=disable_view_after,
        )
        await menu.start()

    async def send(
        self,
        content: str | None = None,
        *,
        tts: bool = False,
        embed: Embed | None = None,
        embeds: Sequence[Embed] | None = None,
        file: File | None = None,
        files: Sequence[File] | None = None,
        stickers: Sequence[GuildSticker | StickerItem] | None = None,
        delete_after: float | None = None,
        nonce: str | int | None = None,
        allowed_mentions: AllowedMentions | None = None,
        reference: Message | MessageReference | PartialMessage | None = None,
        mention_author: bool | None = None,
        view: View | None = None,
        suppress_embeds: bool = False,
        paginate: bool = False,
        post: bool = False,
        no_edit: bool = False,
        ephemeral: bool = False,
    ) -> Message:
        message: Message | None = None
        if content:
            content = str(content)
            for token in self.tokens:
                content = content.replace(token, "[configuration token omitted]")
            if len(content) >= 2000:
                if paginate:
                    return await self.paginate(content, remove_view_after=True)
                if post:
                    return await self.post(content, gist=True)
        if embed:
            if not embed.footer:
                embed.set_footer(
                    text=f"Requested by: {self.author}",
                    icon_url=self.author.display_avatar.url,
                )
                embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            if not embed.color:
                embed.color = await self.fetch_color()

        kwargs: dict[str, any] = {
            "content": content,
            "tts": tts,
            "embed": embed,
            "embeds": embeds,
            "file": file,
            "files": files,
            "stickers": stickers,
            "delete_after": delete_after,
            "nonce": nonce,
            "allowed_mentions": allowed_mentions,
            "reference": reference,
            "mention_author": mention_author,
            "view": view,
            "suppress_embeds": suppress_embeds,
        }

        if self.message.id in self.bot.command_cache and self.message.edited_at and not no_edit:
            try:
                to_pop = (
                    "tts",
                    "file",
                    "files",
                    "stickers",
                    "nonce",
                    "mention_author",
                    "reference",
                    "suppress_embeds",
                )
                for pop in to_pop:
                    kwargs.pop(pop, None)
                kwargs["embed"] = embed
                kwargs["embeds"] = MISSING if embeds is None else embeds
                kwargs["suppress"] = suppress_embeds
                message = await self.bot.command_cache[self.message.id].edit(**kwargs)
            except discord.HTTPException:
                kwargs.pop("suppress", None)
                kwargs["suppress_embeds"] = suppress_embeds
                message = await super().send(**kwargs)

        elif self.interaction is None or self.interaction.is_expired():
            kwargs["reference"] = self.message.to_reference(fail_if_not_exists=False) or reference
            message = await super().send(**kwargs)

        self.bot.command_cache[self.message.id] = message
        if message:
            return message

        kwargs = {
            "content": content,
            "tts": tts,
            "embed": MISSING if embed is None else embed,
            "embeds": MISSING if embeds is None else embeds,
            "file": MISSING if file is None else file,
            "files": MISSING if files is None else files,
            "allowed_mentions": MISSING if allowed_mentions is None else allowed_mentions,
            "view": MISSING if view is None else view,
            "suppress_embeds": suppress_embeds,
            "ephemeral": ephemeral,
        }

        if self.interaction.response.is_done():
            msg = await self.interaction.followup.send(**kwargs, wait=True)
        else:
            await self.interaction.response.send_message(**kwargs)
            msg = await self.interaction.original_message()

        if delete_after is not None and not (ephemeral and self.interaction is not None):
            await msg.delete(delay=delete_after)

        return msg

    def codeblock(self, content: str, language: str = "py") -> str:
        return f"```{language}\n{content}\n```"

    async def confirm(
        self,
        message: Message | None = None,
        embed: Embed | None = None,
        confirm_message: str | None = None,
        *,
        timeout: int = 60,
        delete_after: bool = False,
        no_reply: bool = False,
        remove_view_after: bool = True,
    ) -> ConfirmResult:
        if delete_after:
            remove_view_after = False
        view = ConfirmView(member=self.author, timeout=timeout)
        check_message = confirm_message or 'Press "yes" to accept, or press "no" to deny.'
        if no_reply:
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

    async def can_delete(self, *args, **kwargs) -> Message:
        view = TrashView(member=self.author, ctx=self)
        view.message = await self.send(*args, **kwargs, view=view)


async def setup(bot: Bot) -> None:
    bot.context = Context


async def teardown(bot: Bot) -> None:
    bot.context = commands.Context
