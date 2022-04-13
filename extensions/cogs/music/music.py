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
import typing
from typing import List, Optional, Union

import async_timeout
import discord
import wavelink
from discord.ext import commands, menus
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


class SpotifyTrack(spotify.SpotifyTrack):
    @classmethod
    async def convert(cls, ctx: Context, argument: str):
        decoded = spotify.decode_url(argument)
        if decoded is None:
            raise commands.BadArgument("URL must be a Spotify URL.")

        results = await cls.search(argument, type=decoded["type"])
        if not results:
            raise commands.BadArgument("Could not find any songs matching that query.")
        if decoded["type"] == spotify.SpotifySearchType.track:
            return results[0]
        else:
            return results


class YouTubePlaylist(wavelink.YouTubePlaylist):
    @classmethod
    async def convert(cls, ctx: Context, argument: str):
        results = await cls.search(argument)

        if not results:
            raise commands.BadArgument("Could not find any songs matching that query.")

        return results


class Queue(asyncio.Queue):
    """
    Queue for music.
    """

    def __init__(self, *, max_size: int = 0, allow_duplicates: bool = True):
        super().__init__(maxsize=max_size)
        self._queue: Union[collections.deque, List[Track]] = collections.deque()
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


class Player(wavelink.Player):
    """
    Custom wavelink Player class.
    """

    def __init__(self, *args, context: Context = None, announce: bool = True, allow_duplicates: bool = True, **kwargs):
        self.context: Context = context
        self.youtube_reg = re.compile(
            r"https?://((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
        )
        self.spotify_reg = re.compile(r"https?://open.spotify.com/(?:album|playlist|track)/[a-zA-Z0-9]+")
        super().__init__(*args, **kwargs)
        if self.context:
            self.dj: discord.Member = self.context.author
        self.announce: bool = announce
        self.allow_duplicates: bool = allow_duplicates
        self.queue: Queue = Queue()
        self.waiting: bool = False
        self.loop_song: Optional[Track] = None
        self.pause_votes: set[discord.Member] = set()
        self.resume_votes: set[discord.Member] = set()
        self.skip_votes: set[discord.Member] = set()
        self.shuffle_votes: set[discord.Member] = set()
        self.stop_votes: set[discord.Member] = set()

    async def get_tracks(self, query: str, *, bulk: bool = False) -> typing.Union[Track, typing.List[Track]]:
        """
        Gets tracks from youtube.

        Arguments
        ---------
        query: :class:`str`
            What to search for on youtube or spotify.
        bulk: :class:`bool`
            Whether to return a singular track or all tracks found.

        Returns
        -------
        Track: Union[:class:`Track`, List[:class:`Track`]]
            The track or tracks that were found.
        """
        if self.youtube_reg.match(query):
            try:
                tracks = await self.node.get_tracks(wavelink.YouTubeTrack, query)
            except Exception:
                return await self.node.get_playlist(wavelink.YouTubePlaylist, query)
        elif self.spotify_reg.match(query):
            search_type = spotify.decode_url(query)
            if search_type:
                return await spotify.SpotifyTrack.search(query, type=search_type["type"])
        else:
            tracks = await self.node.get_tracks(wavelink.YouTubeTrack, f"ytsearch:{query}")
        if tracks:
            return tracks if bulk else tracks[0]

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

    async def build_now_playing(self, position: float = None) -> typing.Optional[discord.Embed]:
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
        if self.loop_song:
            next_song = f"[{self.loop_song.title}]({self.loop_song.uri})"
        elif self.queue.up_next:
            next_song = f"[{self.queue.up_next.title}]({self.queue.up_next.uri})"
        else:
            next_song = "Add more songs to the queue!"
        embed.description = (
            f"[{track.title}]({track.uri})\n"
            f"{time}"
            f"> Requester: {track.requester.mention} (`{track.requester}`)\n\n"
            f"Up next: {next_song}"
        )
        if track.thumb:
            embed.set_thumbnail(url=track.thumb)
        return embed

    async def build_added(self, track: Track) -> typing.Optional[discord.Embed]:
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
    def __init__(self, entries, ctx, *, per_page=8):
        super().__init__(entries, per_page=per_page)
        self.ctx = ctx

    async def format_page(self, menu: menus.Menu, page):
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
    def __init__(self, *, options: List[Track]):
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
