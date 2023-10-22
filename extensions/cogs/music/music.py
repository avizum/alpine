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
from typing import Any, TYPE_CHECKING

import async_timeout
import discord
import wavelink
from discord.ext import menus
from wavelink import Playable
from wavelink import Queue as WQueue
from wavelink import YouTubePlaylist, YouTubeTrack
from wavelink.ext import spotify
from wavelink.ext.spotify import SpotifyTrack

from utils import format_seconds, View

from .exceptions import QueueDuplicateTrack

if TYPE_CHECKING:
    from core import Context


URL_REG = re.compile(r"https?://(?:www\.)?.+")


async def do_after(time, coro, *args, **kwargs):
    await asyncio.sleep(time)
    await coro(*args, **kwargs)


class Track(Playable):
    def __init__(
        self,
        *,
        track: Playable | SpotifyTrack,
        context: Context,
    ) -> None:
        self.track: Playable | SpotifyTrack = track
        self.title = track.title
        self.requester: discord.Member = context.author
        self.context: Context = context
        self.uri: str | None = track.uri
        self.thumb: str | None = None
        self.data: Any = {}
        self.hyperlink: str = self.track.title

        if isinstance(track, wavelink.YouTubeTrack):
            self.thumb = track.thumb
            self.data = track.data
        elif isinstance(track, spotify.SpotifyTrack):
            self.title = f"{self.track.title} - {', '.join(track.artists)}"
            self.thumb = track.images[0]
            self.data = track.raw
            uri = track.uri.split(":")
            self.uri = f"https://open.spotify.com/track/{uri[-1]}"

        self.hyperlink = f"[{self.title}]({self.uri})"

    def __repr__(self) -> str:
        return f"Track(title={self.title} requester={self.requester})"


class EventPayload(wavelink.TrackEventPayload):
    """
    Custom wavelink TrackEventPayload class.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.player: Player = kwargs.pop("player")
        self.track: Track = kwargs.pop("track")
        super().__init__(*args, **kwargs)


class Queue(WQueue):
    def __init__(self, *, max_size: int | None = None, allow_duplicates: bool = True) -> None:
        self._queue: collections.deque[Track] = collections.deque(maxlen=max_size)
        self.allow_duplicates: bool = allow_duplicates
        super().__init__()

    @property
    def up_next(self) -> Track | None:
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

    def get(self) -> Track | None:
        return super().get()  # type: ignore # Custom Track Class

    def put(self, item: Track) -> None:
        if not self.allow_duplicates and item in self._queue:
            raise QueueDuplicateTrack
        return self._put(item)  # type: ignore # Custom Track Class


YOUTUBE_REGEX = re.compile(
    r"https?://((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)
URL_REGEX = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")


class Player(wavelink.Player):
    """
    Custom wavelink Player class.
    """

    channel: discord.VoiceChannel | discord.StageChannel

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
        self.track: Track | None = None
        self.dj: discord.Member = self.context.author
        self.bound: discord.TextChannel | discord.VoiceChannel | discord.Thread = self.context.channel
        self.allow_duplicates: bool = allow_duplicates
        self.announce: bool = announce
        self.queue: Queue = Queue(allow_duplicates=allow_duplicates)
        self.waiting: bool = False
        self.loop_song: Track | None = None
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
            except wavelink.WavelinkException:
                return None
        elif search_type:
            tracks = await spotify.SpotifyTrack.search(query)
            if len(tracks) > 1:
                return tracks
            return tracks[0] if tracks else None
        try:
            tracks = await YouTubeTrack.search(query)
            return tracks[0] if tracks else None
        except wavelink.WavelinkException:
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
            self.track = track
            await self.play(track.track)
            if self.announce:
                embed = await self.build_now_playing()
                if embed is None:
                    return
                await self.context.channel.send(embed=embed)

        self.waiting = False

    async def build_now_playing(self, position: float | None = None) -> discord.Embed | None:
        """
        Builds the "now playing" embed
        """
        if not self.track:
            return None
        current = self.track

        embed = discord.Embed(title="Now Playing")
        embed.color = await self.context.fetch_color()

        time = f"Length: {format_seconds(current.track.length/1000)}"
        if position:
            time = f"Position: {format_seconds(position/1000)}/{format_seconds(current.track.length/1000)}"

        if self.queue.up_next:
            next_track = self.queue.up_next
        elif self.loop_song:
            next_track = self.loop_song
        else:
            next_track = None

        # fmt: off
        embed.description = (
            f"{current.hyperlink}\n"
            f"> {time}\n"
            f"> Added by: {current.requester.global_name} ({current.requester})\n"
        )
        # fmt: on
        if next_track:
            next_track_text = (
                f"{next_track.hyperlink}\n"
                f"> Length: {format_seconds(next_track.track.length/1000)}\n"
                f"> Added by: {next_track.requester.global_name} ({next_track.requester})\n"
            )
        else:
            next_track_text = "Nothing - Add something to the queue!"

        if current.thumb:
            embed.set_thumbnail(url=current.thumb)

        embed.add_field(name="Up Next", value=next_track_text)
        return embed

    async def build_added(self, source: Track) -> discord.Embed:
        """
        Builds the "added song to queue" embed.
        """
        original = source
        embed = discord.Embed(title="Added to queue")
        embed.description = f"Song: {original.hyperlink}"
        embed.set_thumbnail(url=original.thumb)

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
