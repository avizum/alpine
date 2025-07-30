"""
[Alpine Bot]
Copyright (C) 2021 - 2025 avizum

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
import sys
from typing import Any, Generic, overload, Sequence, TYPE_CHECKING, TypeVar

import discord
from asyncgist import File as AGFile
from discord import ui
from discord.ext import commands, menus
from discord.utils import MISSING

from utils.emojis import Emojis
from utils.helpers import EMOJI_REGEX
from utils.paginators import Paginator, WrappedPaginator
from utils.views import View as AView

if TYPE_CHECKING:
    from asyncpg import Pool
    from discord import AllowedMentions, Embed, File, GuildSticker, Message, MessageReference, PartialMessage, StickerItem
    from discord.ui.view import BaseView

    from extensions.cogs.music.cog import Player
    from utils import Database

    from .alpine import Bot

__all__ = (
    "ConfirmResult",
    "Context",
)

BotT_co = TypeVar("BotT_co", bound="commands.Bot | commands.AutoShardedBot", covariant=True)
T = TypeVar("T")


class TrashView(AView):
    message: discord.Message

    def __init__(self, *, member: discord.Member, timeout: int = 60, ctx: Context) -> None:
        self.ctx: Context = ctx
        super().__init__(member=member, timeout=timeout)

    async def stop(self) -> None:
        for button in self.children:
            if isinstance(button, discord.ui.Button):
                button.disabled = True
        try:
            await self.message.edit(view=None)
        except discord.NotFound:
            pass
        super().stop()

    async def on_timeout(self) -> None:
        await self.stop()

    @discord.ui.button(emoji="\U0001f5d1", style=discord.ButtonStyle.danger)
    async def trash(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.message.delete()
        if self.ctx.interaction:
            return
        await self.ctx.message.add_reaction(Emojis.GREEN_TICK)


class ConfirmView(AView):
    def __init__(self, *, member: discord.Member | discord.User, timeout: int | float) -> None:
        super().__init__(member=member, timeout=timeout)
        self.value: bool | None = None
        self.message: Message | None = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        self.value = True
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        self.value = False
        self.stop()


class ConfirmResult:
    def __init__(self, message: discord.Message, result: bool | None) -> None:
        self.message: discord.Message = message
        self.result: bool | None = result

    def __repr__(self) -> str:
        return f"<ConfirmResult result={self.result}>"


class AutoPageSource(menus.ListPageSource):
    def __init__(self, entry: str | list | commands.Paginator, language: str = "", *, limit: int = 1000) -> None:
        if isinstance(entry, str):
            pag = WrappedPaginator(prefix=f"```{language}", suffix="```", max_size=limit, force_wrap=True)
            pag.add_line(entry)
            entry = pag.pages
        elif isinstance(entry, commands.Paginator):
            entry = entry.pages
        super().__init__(entry, per_page=1)

    async def format_page(self, menu: menus.Menu, page: T) -> T:
        return page


class Context(commands.Context, Generic[BotT_co]):
    author: discord.Member
    guild: discord.Guild
    channel: discord.TextChannel | discord.VoiceChannel | discord.Thread
    bot: Bot
    me: discord.Member
    command: commands.Command
    prefix: str
    voice_client: Player

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.locally_handled: bool = False
        if self.interaction:
            self.message.content = f"/{self.invoked_with}"
        tokens: list[str] = []
        tokens.extend(self.bot.settings["bot_tokens"].values())
        tokens.extend(self.bot.settings["api_tokens"].values())
        tokens.extend(self.bot.settings["webhooks"].values())
        self.tokens: list[str] = tokens

    @property
    def database(self) -> Database:
        return self.bot.database

    @property
    def pool(self) -> Pool:
        return self.bot.database.pool

    @property
    def clean_prefix(self) -> str:
        match = EMOJI_REGEX.match(self.prefix)
        if match:
            return re.sub(EMOJI_REGEX, match[2], self.prefix)

        return re.sub(f"<@!?{self.bot.user.id}>", f"@{self.me.display_name} ", self.prefix)

    @property
    def content(self) -> str:
        return self.message.content

    @property
    def reference(self) -> Message | None:
        ref = self.message.reference
        if ref and isinstance(ref.resolved, discord.Message):
            return ref.resolved
        return None

    async def post(self, *, content: str, filename: str) -> str | None:
        gist_file = [AGFile(filename=filename, content=content)]
        posted_gist = await self.bot.gist.post_gist(description=str(self.author), files=gist_file, public=True)

        return None if posted_gist.html_url is None else f"<{posted_gist.html_url}>"

    async def fetch_color(self, member: discord.Member | discord.User | None = None) -> discord.Color:
        member = member or self.author
        data = await self.database.fetch_user(member.id)
        color = None
        if data is not None and data.color is not None:
            color = discord.Color(data.color)
        if not color:
            color = member.color
        if color == discord.Color(0):
            color = discord.Color(0x2F3136)
            if await self.bot.is_owner(member):
                color = discord.Color(0x01B9C0)
        return color

    def get_color(self, member: discord.Member | discord.User | None = None) -> discord.Color:
        member = member or self.author
        data = self.database.get_user(member.id)
        color = None
        if data is not None and data.color is not None:
            color = discord.Color(data.color)
        if not color:
            color = member.color
        elif color == discord.Color(0):
            color = discord.Color(0x2F3136)
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
    ) -> Message:
        lang = lang or ""
        menu = Paginator(
            AutoPageSource(entry, lang, limit=limit),
            ctx=self,
            remove_view_after=remove_view_after,
            delete_message_after=delete_message_after,
            disable_view_after=disable_view_after,
        )
        return await menu.start()

    async def send_and_cache(self, *args: Any, **kwargs: Any) -> Message:
        message = await super().send(*args, **kwargs)
        self.bot.command_cache[self.message.id] = message
        return message

    async def edit_and_recache(self, message: discord.Message, *args: Any, **kwargs: Any) -> Message:
        message = await message.edit(*args, **kwargs)
        self.bot.command_cache[self.message.id] = message
        return message

    @overload
    async def send(
        self,
        *,
        file: discord.File = ...,
        delete_after: float = ...,
        nonce: str | int = ...,
        allowed_mentions: discord.AllowedMentions = ...,
        reference: discord.Message | discord.MessageReference | discord.PartialMessage = ...,
        mention_author: bool = ...,
        view: ui.LayoutView,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> discord.Message: ...

    @overload
    async def send(
        self,
        *,
        files: Sequence[discord.File] = ...,
        delete_after: float = ...,
        nonce: str | int = ...,
        allowed_mentions: discord.AllowedMentions = ...,
        reference: discord.Message | discord.MessageReference | discord.PartialMessage = ...,
        mention_author: bool = ...,
        view: ui.LayoutView,
        suppress_embeds: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
    ) -> discord.Message: ...

    @overload
    async def send(
        self,
        content: str | None = ...,
        *,
        tts: bool = ...,
        embed: discord.Embed = ...,
        file: discord.File = ...,
        stickers: Sequence[discord.GuildSticker | discord.StickerItem] = ...,
        delete_after: float = ...,
        nonce: str | int = ...,
        allowed_mentions: discord.AllowedMentions = ...,
        reference: discord.Message | discord.MessageReference | discord.PartialMessage = ...,
        mention_author: bool = ...,
        view: ui.View = ...,
        suppress_embeds: bool = ...,
        paginate: bool = ...,
        post: bool = ...,
        no_edit: bool = ...,
        no_reply: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
        poll: discord.Poll = ...,
    ) -> discord.Message: ...

    @overload
    async def send(
        self,
        content: str | None = ...,
        *,
        tts: bool = ...,
        embed: discord.Embed = ...,
        files: Sequence[discord.File] = ...,
        stickers: Sequence[discord.GuildSticker | discord.StickerItem] = ...,
        delete_after: float = ...,
        nonce: str | int = ...,
        allowed_mentions: discord.AllowedMentions = ...,
        reference: discord.Message | discord.MessageReference | discord.PartialMessage = ...,
        mention_author: bool = ...,
        view: ui.View = ...,
        suppress_embeds: bool = ...,
        paginate: bool = ...,
        post: bool = ...,
        no_edit: bool = ...,
        no_reply: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
        poll: discord.Poll = ...,
    ) -> discord.Message: ...

    @overload
    async def send(
        self,
        content: str | None = ...,
        *,
        tts: bool = ...,
        embeds: Sequence[discord.Embed] = ...,
        file: discord.File = ...,
        stickers: Sequence[discord.GuildSticker | discord.StickerItem] = ...,
        delete_after: float = ...,
        nonce: str | int = ...,
        allowed_mentions: discord.AllowedMentions = ...,
        reference: discord.Message | discord.MessageReference | discord.PartialMessage = ...,
        mention_author: bool = ...,
        view: ui.View = ...,
        suppress_embeds: bool = ...,
        paginate: bool = ...,
        post: bool = ...,
        no_edit: bool = ...,
        no_reply: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
        poll: discord.Poll = ...,
    ) -> discord.Message: ...

    @overload
    async def send(
        self,
        content: str | None = ...,
        *,
        tts: bool = ...,
        embeds: Sequence[discord.Embed] = ...,
        files: Sequence[discord.File] = ...,
        stickers: Sequence[discord.GuildSticker | discord.StickerItem] = ...,
        delete_after: float = ...,
        nonce: str | int = ...,
        allowed_mentions: discord.AllowedMentions = ...,
        reference: discord.Message | discord.MessageReference | discord.PartialMessage = ...,
        mention_author: bool = ...,
        view: ui.View = ...,
        suppress_embeds: bool = ...,
        paginate: bool = ...,
        post: bool = ...,
        no_edit: bool = ...,
        no_reply: bool = ...,
        ephemeral: bool = ...,
        silent: bool = ...,
        poll: discord.Poll = ...,
    ) -> discord.Message: ...

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
        view: BaseView | None = None,
        suppress_embeds: bool = False,
        paginate: bool = False,
        post: bool = False,
        no_edit: bool = False,
        no_reply: bool = False,
        ephemeral: bool = False,
        silent: bool = False,
        poll: discord.Poll = MISSING,
    ) -> Message:
        if content:
            content = str(content)
            for token in self.tokens:
                content = content.replace(token, "[configuration token omitted]")
            for path in sys.path:
                content = content.replace(path, "[PATH]")
            if len(content) >= 2000:
                if paginate:
                    return await self.paginate(content, remove_view_after=True)
                if post:
                    content = f"Output too long, posted here: {await self.post(filename='output.py', content=content)}"

        if embed:
            if not embed.footer and not self.interaction and not self.message.to_reference(fail_if_not_exists=False):
                embed.set_footer(
                    text=f"Requested by: {self.author}",
                    icon_url=self.author.display_avatar.url,
                )
                embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
            if not embed.color:
                embed.color = await self.fetch_color()

        if ephemeral and self.interaction:
            no_reply = True

        kwargs: dict[str, Any] = {
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
            "silent": silent,
            "poll": poll,
        }

        if self.message.id in self.bot.command_cache and self.message.edited_at and not no_edit:
            edit_kwargs = kwargs.copy()
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
                    "silent",
                    "poll",
                )
                for pop in to_pop:
                    edit_kwargs.pop(pop, None)
                edit_kwargs["embed"] = embed
                edit_kwargs["embeds"] = MISSING if embeds is None else embeds
                edit_kwargs["suppress"] = suppress_embeds
                message = self.bot.command_cache[self.message.id]
                return await self.edit_and_recache(message, **edit_kwargs)
            except discord.HTTPException:
                return await self.send_and_cache(**kwargs)

        if self.interaction is None or self.interaction.is_expired():
            kwargs["reference"] = self.message.to_reference(fail_if_not_exists=False) or reference
            if no_reply:
                kwargs["reference"] = None
            return await self.send_and_cache(**kwargs)

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
            "silent": silent,
            "poll": poll,
        }

        if self.interaction.response.is_done():
            msg = await self.interaction.followup.send(**kwargs, wait=True)
        else:
            await self.interaction.response.send_message(**kwargs)
            msg = await self.interaction.original_response()

        if delete_after is not None:
            await msg.delete(delay=delete_after)

        return msg

    def codeblock(self, content: str, language: str = "py") -> str:
        return f"```{language}\n{content}\n```"

    async def confirm(
        self,
        *,
        message: str | None = None,
        embed: Embed = MISSING,
        confirm_messsage: str = 'Press "yes" to accept, or press "no" to deny',
        timeout: int = 60,  # noqa: ASYNC109
        delete_message_after: bool = False,
        remove_view_after: bool = False,
        no_reply: bool = False,
        ephemeral: bool = False,
        **kwargs: Any,
    ) -> ConfirmResult:
        if delete_message_after and remove_view_after:
            raise ValueError("Cannot have both delete_message_after and remove_view_after keyword arguments.")
        if (embed and message) or embed:
            embed.description = f"{embed.description}\n\n{confirm_messsage}" if embed.description else confirm_messsage
        elif message:
            message = f"{message}\n\n{confirm_messsage}"
        view = ConfirmView(member=self.author, timeout=timeout)
        msg = await self.send(content=message, embed=embed, no_reply=no_reply, ephemeral=ephemeral, view=view, **kwargs)
        view.message = msg
        await view.wait()
        if delete_message_after:
            await msg.delete()
        if remove_view_after:
            await msg.edit(view=None)
        return ConfirmResult(msg, view.value)

    async def can_delete(self, *args, timeout: int = 60, **kwargs) -> Message:  # noqa: ASYNC109
        if self.interaction:
            return await self.send(*args, **kwargs)
        view = TrashView(member=self.author, timeout=timeout, ctx=self)
        message = await self.send(*args, **kwargs, view=view)
        view.message = message
        return message


async def setup(bot: Bot) -> None:
    bot.context = Context


async def teardown(bot: Bot) -> None:
    bot.context = commands.Context
