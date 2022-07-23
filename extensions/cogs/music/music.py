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

import asyncio
import collections
import re

import async_timeout
import discord
import wavelink
from wavelink import Track as WLTrack, PartialTrack as WLPTrack
from discord.ext import menus
from wavelink.ext import spotify

from core import Bot, Context
from utils import View, format_seconds

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


class Queue(asyncio.Queue):
    """
    Queue for music.
    """

    def __init__(self, *, max_size: int = 0, allow_duplicates: bool = True):
        super().__init__(maxsize=max_size)
        self._queue: collections.deque | list[Track] = collections.deque()
        self.allow_duplicates = allow_duplicates

    def __contains__(self, item):
        return item in self._queue

    def _put(self, item, left=False):
        if not self.allow_duplicates and item in self._queue:
            return
        meth = self._queue.appendleft if left is True else self._queue.append
        meth(item)

    def remove(self, track):
        self._queue.remove(track)

    def remove_at_index(self, index: int):
        self._queue.pop(index)

    def clear(self):
        self._queue.clear()

    async def put(self, item, left=False):
        """
        Put an item into the queue.
        Put an item into the queue. If the queue is full, wait until a free
        slot is available before adding item.
        """
        while self.full():
            putter = self._get_loop().create_future()
            self._putters.append(putter)
            try:
                await putter
            except Exception:
                putter.cancel()
                try:
                    self._putters.remove(putter)
                except ValueError:
                    pass
                if not self.full() and not putter.cancelled():
                    self._wakeup_next(self._putters)
                raise
        return self.put_nowait(item, left=left)

    def put_nowait(self, item, left=False) -> None:
        if self.full():
            raise asyncio.QueueFull
        self._put(item, left=left)
        self._unfinished_tasks += 1
        self._finished.clear()
        self._wakeup_next(self._getters)

    @property
    def up_next(self):
        return self._queue[0] if self.size else None

    @property
    def size(self):
        return len(self._queue)


class Track(wavelink.Track):
    """Wavelink Track object with a requester attribute."""

    __slots__ = ("requester",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.thumb = kwargs.get("thumb")
        self.requester = kwargs.get("requester")

        hyperlinked_title = f"[{self.title}]({self.uri})" if self.uri is not None else self.title
        self.hyperlinked_title = hyperlinked_title


YOUTUBE_REGEX = re.compile(
    r"https?://((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)

class Player(wavelink.Player):
    """
    Custom wavelink Player class.
    """

    def __init__(
        self,
        *args,
        context: Context = None,
        announce: bool = True,
        allow_duplicates: bool = True,
        **kwargs,
    ):
        self.context: Context = context
        super().__init__(*args, **kwargs)
        if self.context:
            self.dj: discord.Member = self.context.author
            self.bound: discord.TextChannel = self.context.channel
        self.announce: bool = announce
        self.allow_duplicates: bool = allow_duplicates
        self.queue: Queue = Queue()
        self.waiting: bool = False
        self.loop_song: Track | None = None
        self.pause_votes: set[discord.Member] = set()
        self.resume_votes: set[discord.Member] = set()
        self.skip_votes: set[discord.Member] = set()
        self.shuffle_votes: set[discord.Member] = set()
        self.stop_votes: set[discord.Member] = set()

    async def connect(self, *, timeout: float, reconnect: bool, **kwargs) -> None:
        return await super().connect(timeout=timeout, reconnect=reconnect)

    async def get_tracks(self, query: str) -> WLTrack | WLPTrack | list[WLTrack | WLPTrack]:
        search_type = spotify.decode_url(query)

        if YOUTUBE_REGEX.match(query):
            try:
                tracks = await self.node.get_tracks(wavelink.YouTubeTrack, query)
            except Exception:
                return await self.node.get_playlist(wavelink.YouTubePlaylist, query)
        elif search_type:
            if search_type["type"] in [
                spotify.SpotifySearchType.album,
                spotify.SpotifySearchType.playlist,
            ]:
                full = []
                async for partial in spotify.SpotifyTrack.iterator(
                    query=query, type=search_type["type"], partial_tracks=True
                ):
                    full.append(partial)
                return full
            return await spotify.SpotifyTrack.search(query, type=search_type["type"], return_first=True)
        else:
            tracks = await self.node.get_tracks(wavelink.YouTubeTrack, f"ytsearch:{query}")
        if tracks:
            return tracks[0]

    async def do_next(self) -> None:
        if self.waiting:
            return

        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        try:
            self.waiting = True
            if not self.loop_song:
                with async_timeout.timeout(120):
                    track = await self.queue.get()
            if self.loop_song:
                track = self.loop_song
        except asyncio.TimeoutError:
            if self.context:
                await self.context.send("Disconnecting due to inactivity.")
            return await self.disconnect()

        await self.play(track)
        self.waiting = False
        if self.announce:
            await self.context.channel.send(embed=await self.build_now_playing())

    async def build_now_playing(self, position: float = None) -> discord.Embed | None:
        """
        Builds the "now playing" embed
        """
        track: Track = self.source
        if not track:
            return

        embed = discord.Embed(title="Now Playing")
        if self.context:
            embed.color = await self.context.fetch_color()
        time = f"> Length: {format_seconds(track.length)}\n"
        if position:
            time = f"> Position {format_seconds(position)}/{format_seconds(track.length)}\n"
        if isinstance(self.queue.up_next, wavelink.PartialTrack):
            next_song = self.queue.up_next.title
        elif self.loop_song:
            next_song = self.loop_song.hyperlinked_title
        elif self.queue.up_next:
            next_song = self.queue.up_next.hyperlinked_title
        else:
            next_song = "Add more songs to the queue!"

        # Happens when Spotify playlist is added to the queue
        # Partial tracks become Youtube tracks when played
        if isinstance(track, wavelink.YouTubeTrack):
            embed.description = f"[{track.title}]({track.uri})\n" f"{time}\n" f"Up next: {next_song}"
            if track.thumb:
                embed.set_thumbnail(url=track.thumb)
            return embed
        embed.description = (
            f"{track.hyperlinked_title}\n"
            f"{time}"
            f"> Requester: {track.requester.mention} (`{track.requester}`)\n\n"
            f"Up next: {next_song}"
        )
        if track.thumb:
            embed.set_thumbnail(url=track.thumb)
        return embed

    async def build_added(self, track: Track) -> discord.Embed | None:
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
        if self.ctx.guild.icon.url:
            embed.set_thumbnail(url=self.ctx.guild.icon.url)
        return embed


class SearchView(View):
    def __init__(self, *, ctx: Context):
        self.ctx = ctx
        self.option = None
        super().__init__(member=ctx.author, timeout=180)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop_view(self, interaction: discord.Interaction, button: discord.Button):
        await self.ctx.message.delete()
        await self.stop()


class SearchSelect(discord.ui.Select):
    def __init__(self, *, options: list[Track]):
        options = [discord.SelectOption(label=f"{number+1}) {track.title}") for number, track in enumerate(options)]
        super().__init__(
            placeholder="Select the songs you want to play",
            options=options,
            min_values=1,
            max_values=1,
            disabled=False,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.option = self.values
        self.view.stop()
