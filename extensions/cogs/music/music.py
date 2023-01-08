"""
[Avimetry Bot]
Copyright (C) 2021 - 2023 avizum

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
import collections
import re
from typing import TYPE_CHECKING, Any

import async_timeout
import discord
import wavelink
from wavelink import (
    YouTubeTrack,
    YouTubePlaylist,
    WaitQueue,
)
from discord.ext import menus
from wavelink.ext import spotify
from wavelink.ext.spotify import SpotifyTrack

from utils import View, format_seconds
from .exceptions import QueueDuplicateTrack

if TYPE_CHECKING:
    from wavelink import PartialTrack
    from wavelink.abc import Playable

    from core import Bot, Context


URL_REG = re.compile(r"https?://(?:www\.)?.+")


async def do_after(time, coro, *args, **kwargs):
    await asyncio.sleep(time)
    await coro(*args, **kwargs)


class IsResponding:
    def __init__(self, emoji: str, message: discord.Message, bot: Bot) -> None:
        self.task = None
        self.message = message
        self.bot = bot
        self.emoji = emoji

    async def __aenter__(self):
        self.task = self.bot.loop.create_task(do_after(5, self.message.add_reaction, self.emoji))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.task:
            self.task.cancel()


class Queue(WaitQueue):
    def __init__(
        self, *, max_size: int | None = None, history_max_size: int | None = None, allow_duplicates: bool = True
    ) -> None:
        self._queue: collections.deque[Track | PartialTrack] = collections.deque()
        self.allow_duplicates: bool = allow_duplicates
        super().__init__(max_size=max_size, history_max_size=history_max_size)

    @property
    def up_next(self) -> Track | PartialTrack | None:
        """
        Returns the next track in the queue.
        """
        return self._queue[0] if self.count else None

    @property
    def size(self) -> int:
        """
        Returns the amount of tracks in the queue.
        """
        return len(self._queue)

    def put(self, item: Playable) -> None:
        if not self.allow_duplicates and item in self._queue:
            raise QueueDuplicateTrack
        return super().put(item)


class Track(wavelink.Track):
    """Wavelink Track object with a requester attribute."""

    __slots__ = ("requester", "thumb", "hyperlinked_title")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args)

        self.thumb = kwargs.get("thumb")
        self.requester = kwargs.get("requester")

        hyperlinked_title = f"[{self.title}]({self.uri})" if self.uri is not None else self.title
        self.hyperlinked_title = hyperlinked_title


YOUTUBE_REGEX = re.compile(
    r"https?://((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)
URL_REGEX = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")


class Player(wavelink.Player):
    """
    Custom wavelink Player class.
    """

    source: Track | PartialTrack | None

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
        self.queue: Queue = Queue(allow_duplicates=allow_duplicates)
        self.waiting: bool = False
        self.loop_song: Playable | None = None
        self.pause_votes: set[discord.Member] = set()
        self.resume_votes: set[discord.Member] = set()
        self.skip_votes: set[discord.Member] = set()
        self.shuffle_votes: set[discord.Member] = set()
        self.stop_votes: set[discord.Member] = set()

    async def get_tracks(self, query: str) -> Playable | SpotifyTrack | list[Playable] | list[SpotifyTrack] | None:
        search_type = spotify.decode_url(query)

        if YOUTUBE_REGEX.match(query):
            try:
                tracks = await YouTubeTrack.search(query)
                if isinstance(tracks, YouTubePlaylist):
                    return tracks
                return tracks[0] if tracks else None
            except wavelink.LoadTrackError:
                return None
        elif search_type:
            try:
                if search_type["type"] in [
                    spotify.SpotifySearchType.album,
                    spotify.SpotifySearchType.playlist,
                ]:
                    return [
                        partial
                        async for partial in SpotifyTrack.iterator(
                            query=query, type=search_type["type"], partial_tracks=True
                        )
                    ]
                return await SpotifyTrack.search(query, type=search_type["type"], return_first=True)
            except spotify.SpotifyRequestError:
                return None
        try:
            tracks = await YouTubeTrack.search(query)
            return tracks[0] if tracks else None
        except wavelink.LoadTrackError:
            return None

    async def do_next(self) -> None:
        if self.waiting:
            return

        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        track = None

        try:
            self.waiting = True
            if not self.loop_song:
                with async_timeout.timeout(120):
                    track = self.queue.get()
            if self.loop_song:
                track = self.loop_song
        except wavelink.QueueEmpty:
            self.waiting = True
        except asyncio.TimeoutError:
            if self.context:
                await self.context.send("Disconnecting due to inactivity.")
            return await self.disconnect()

        if track is not None:
            await self.play(track)

        self.waiting = False
        if self.announce:
            embed = await self.build_now_playing()
            if embed is None:
                return
            await self.context.channel.send(embed=embed)

    async def build_now_playing(self, position: float | None = None) -> discord.Embed | None:
        """
        Builds the "now playing" embed
        """
        if not self.source:
            return
        track = self.source

        embed = discord.Embed(title="Now Playing")
        embed.color = await self.context.fetch_color()

        time = f"> Length: {format_seconds(track.length)}\n"
        if position:
            time = f"> Position {format_seconds(position)}/{format_seconds(track.length)}\n"

        if self.queue.up_next:
            if isinstance(self.queue.up_next, Track):
                next_track = self.queue.up_next.hyperlinked_title
            else:
                next_track = self.queue.up_next.title
        elif self.loop_song:
            if isinstance(self.queue.up_next, Track):
                next_track = self.loop_song.hyperlinked_title
            else:
                next_track = self.loop_song.title
        else:
            next_track = "Add more songs to the queue!"
        # Happens when Spotify playlist is added to the queue
        # Partial tracks become Youtube tracks when played
        if isinstance(track, wavelink.YouTubeTrack):
            embed.description = f"[{track.title}]({track.uri})\n" f"{time}\n" f"Up next: {next_track}"
            if track.thumb:
                embed.set_thumbnail(url=track.thumb)
            return embed
        embed.description = (
            f"{track.hyperlinked_title}\n"
            f"{time}"
            f"> Requester: {track.requester.mention} (`{track.requester}`)\n\n"
            f"Up next: {next_track}"
        )
        if track.thumb:
            embed.set_thumbnail(url=track.thumb)
        return embed

    async def build_added(self, track: Track) -> discord.Embed:
        """
        Builds the "added song to queue" embed.
        """
        embed = discord.Embed(title="Added to queue")
        embed.description = f"Song: [{track.title}]({track.uri})"
        if track.thumb:
            embed.set_thumbnail(url=track.thumb)
        return embed

    async def disconnect(self, *, force: bool = False) -> None:
        self.queue.clear()
        await self.stop()
        return await super().disconnect(force=force)


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
    def __init__(self, *, options: list[Track]):
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
