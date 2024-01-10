"""
[Avimetry Bot]
Copyright (C) 2021 - 2024 avizum

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

import asyncio
import re
from typing import TYPE_CHECKING, Any, cast

import discord
import wavelink
from discord.ext import menus
from wavelink import Playable as WPlayable
from wavelink import Playlist as WPlaylist
from wavelink import Queue as WQueue

from utils import View, format_seconds

if TYPE_CHECKING:
    from core import Context


URL_REG = re.compile(r"https?://(?:www\.)?.+")


async def do_after(time, coro, *args, **kwargs):
    await asyncio.sleep(time)
    await coro(*args, **kwargs)


class Playable(WPlayable):
    requester: discord.Member | str
    hyperlink: str


class Playlist(WPlaylist):
    tracks: list[Playable]


class Queue(WQueue):
    @property
    def up_next(self) -> Playable | None:
        """
        Returns the next track in the queue.
        """
        return cast(Playable, self._queue[0] if self else None)

    @property
    def size(self) -> int:
        """
        Returns the amount of tracks in the queue.
        """
        return len(self._queue)

    def get(self) -> Playable:
        return cast(Playable, super().get())

    def _put_left(self, item: Playable) -> None:
        self._check_compatability(item)
        self._queue.appendleft(Playable)  # type: ignore

    def put_left(self, item: Playable | Playlist, /, *, atomic: bool = True) -> int:
        added: int = 0

        if isinstance(item, WPlaylist):
            if atomic:
                self._check_atomic(item)

            for track in item:
                try:
                    self._put_left(track)  # type: ignore
                    added += 1
                except TypeError:
                    pass
        else:
            self._put_left(item)
            added += 1
        return added

    async def put_left_wait(self, item: Playable | Playlist, /, *, atomic: bool = True) -> int:
        added: int = 0

        async with self._lock:
            if isinstance(item, (list, Playlist)):
                if atomic:
                    super()._check_atomic(item)

                for track in item:
                    try:
                        self._put_left(track)  # type: ignore
                        added += 1
                    except TypeError:
                        pass

                    await asyncio.sleep(0)

            else:
                self._put_left(item)
                added += 1
                await asyncio.sleep(0)

        self._wakeup_next()
        return added


class Player(wavelink.Player):
    """
    Custom wavelink Player class.
    """

    channel: discord.VoiceChannel | discord.StageChannel
    current: Playable | None
    queue: Queue

    def __call__(self, client: discord.Client, channel: discord.VoiceChannel | discord.StageChannel) -> Player:
        super(wavelink.Player, self).__init__(client, channel)

        return self

    def __init__(
        self,
        *args: Any,
        context: Context,
        announce: bool = True,
        allow_duplicates: bool = True,
        **kwargs: Any,
    ) -> None:
        self.context: Context = context
        super().__init__(*args, **kwargs)
        self.dj: discord.Member = self.context.author
        self.bound: discord.TextChannel | discord.VoiceChannel | discord.Thread = self.context.channel
        self.allow_duplicates: bool = allow_duplicates
        self.announce: bool = announce
        self.queue: Queue = Queue()
        self.waiting: bool = False
        self.pause_votes: set[discord.Member] = set()
        self.resume_votes: set[discord.Member] = set()
        self.skip_votes: set[discord.Member] = set()
        self.shuffle_votes: set[discord.Member] = set()
        self.stop_votes: set[discord.Member] = set()

    async def skip(self) -> Playable | None:
        return await super().skip(force=False)  # type: ignore

    async def stop(self, *, force: bool = True) -> Playable | None:
        return await super().skip(force=force)  # type: ignore

    async def fetch_tracks(self, query: str) -> Playable | Playlist | None:
        try:
            tracks = cast(list[Playable] | Playlist, await Playable.search(query))
        except wavelink.LavalinkLoadException:
            tracks = None

        if not tracks:
            return

        return tracks if isinstance(tracks, WPlaylist) else tracks[0]

    async def clear_votes(self) -> None:
        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

    async def build_now_playing(self, position: float | None = None) -> discord.Embed | None:
        """
        Builds the "now playing" embed
        """
        if not self.current:
            return None
        current = self.current

        embed = discord.Embed(title="Now Playing")
        embed.color = await self.context.fetch_color()

        time = f"Length: {format_seconds(current.length/1000)}"
        if position:
            time = f"Position: {format_seconds(position/1000)}/{format_seconds(current.length/1000)}"

        if self.queue.up_next:
            next_track = self.queue.up_next
        else:
            next_track = None

        # fmt: off
        embed.description = (
            f"{current.hyperlink}\n"
            f"> {time}\n"
            f"> Added by: {current.requester}\n"
        )
        # fmt: on
        if next_track:
            next_track_text = (
                f"{next_track.hyperlink}\n"
                f"> Length: {format_seconds(next_track.length/1000)}\n"
                f"> Added by: {next_track.requester}\n"
            )
        else:
            next_track_text = "Nothing - Add something to the queue!"

        if current.artwork:
            embed.set_thumbnail(url=current.artwork)

        embed.add_field(name="Up Next", value=next_track_text)
        return embed

    async def build_added(self, source: Playable) -> discord.Embed:
        """
        Builds the "added song to queue" embed.
        """
        original = source
        embed = discord.Embed(title="Added to queue")
        embed.description = f"Song: {original.hyperlink}"
        embed.set_thumbnail(url=original.artwork)

        return embed

    async def disconnect(self, *, force: bool = False) -> None:
        self.queue.clear()
        return await super().disconnect()


class PaginatorSource(menus.ListPageSource):
    def __init__(self, entries: list[str], ctx: Context, *, per_page=8):
        super().__init__(entries, per_page=per_page)
        self.ctx = ctx

    async def format_page(self, menu: menus.Menu, page: list[str]):
        embed = discord.Embed(title=f"Queue for {self.ctx.guild}", color=await self.ctx.fetch_color())
        embed.description = "\n".join(page)
        if self.ctx.guild.icon:
            embed.set_thumbnail(url=self.ctx.guild.icon.url)
        return embed


class SearchView(View):
    def __init__(self, *, ctx: Context):
        self.ctx = ctx
        self.option: list[str] | None = None
        super().__init__(member=ctx.author, timeout=180)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop_view(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ctx.message.delete()
        self.stop()


class SearchSelect(discord.ui.Select[SearchView]):
    def __init__(self, *, options: list[Playable]):
        select_options = [discord.SelectOption(label=f"{number+1}) {track.title}") for number, track in enumerate(options)]
        super().__init__(
            placeholder="Select the songs you want to play",
            options=select_options,
            min_values=1,
            max_values=1,
            disabled=False,
        )

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        await interaction.response.defer()
        self.view.option = self.values
        self.view.stop()
