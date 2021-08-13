"""
Cog for music powered by Lavalink with Wavelink.
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
import async_timeout
import discord
import math
import random
import re
import typing
import wavelink
import collections

from utils import core
from utils import AvimetryContext, AvimetryPages, format_seconds
from discord.ext import commands, menus

URL_REG = re.compile(r'https?://(?:www\.)?.+')


class Queue(asyncio.Queue):
    """
    Queue for music.
    """
    def __init__(self, max_size=0):
        super().__init__(maxsize=max_size)
        self._queue = collections.deque()

    def _put(self, item, left=False):
        meth = self._queue.appendleft if left is True else self._queue.append
        meth(item)

    def remove(self, track):
        self._queue.remove(track)

    def clear(self):
        self._queue.clear()

    async def put(self, item, left=False):
        """Put an item into the queue.
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
        if not self.size:
            return None
        return self._queue[0]

    @property
    def size(self):
        return len(self._queue)


class NoChannelProvided(commands.CommandError):
    """Error raised when no suitable voice channel was supplied."""
    pass


class IncorrectChannelError(commands.CommandError):
    """Error raised when commands are issued outside of the players session channel."""
    pass


class NotDJ(commands.CheckFailure):
    """
    Error raised when someone tries do to something when they are not DJ.
    """
    pass


class Track(wavelink.Track):
    """Wavelink Track object with a requester attribute."""

    __slots__ = ('requester', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args)

        self.thumb = kwargs.get('thumb', None)
        self.requester = kwargs.get('requester')


class Player(wavelink.Player):
    """Custom wavelink Player class."""

    def __init__(self, *args, context=None, **kwargs):
        self.context: AvimetryContext = context
        super().__init__(*args, **kwargs)

        if self.context:
            self.dj: discord.Member = self.context.author

        self.queue = Queue()

        self.waiting = False
        self.updating = False

        self.pause_votes = set()
        self.resume_votes = set()
        self.skip_votes = set()
        self.shuffle_votes = set()
        self.stop_votes = set()

    async def do_next(self) -> None:
        if self.is_playing() or self.waiting:
            return

        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        try:
            self.waiting = True
            with async_timeout.timeout(120):
                track = await self.queue.get()
        except asyncio.TimeoutError:
            return await self.teardown()

        await self.play(track)
        self.waiting = False

        await self.context.channel.send(embed=await self.build_now_playing())

    async def build_now_playing(self, position=None) -> typing.Optional[discord.Embed]:
        """
        Builds the "now playing" embed
        """
        track: Track = self.source
        if not track:
            return

        embed = discord.Embed(title='Now Playing')
        if self.context:
            embed.color = await self.context.determine_color()
        time = f'Length: {format_seconds(track.length)}\n\n'
        if position:
            time = f'Position {format_seconds(position)}/{format_seconds(track.length)}\n\n'
        embed.description = (
            f'Song: [{track.title}]({track.uri})\n\n'
            f'{time}'
            f"Requested by: {track.requester.mention} (`{track.requester}`)\n\n"
            f"Up next: {self.queue.up_next or 'Add more songs!'}"
        )
        if track.thumb:
            embed.set_thumbnail(url=track.thumb)
        return embed

    async def build_added(self, track: Track) -> typing.Optional[discord.Embed]:
        """
        Builds the "added song to queue" embed.
        """
        embed = discord.Embed(title="Added to queue")
        embed.description = (
            f"Song: [{track.title}]({track.uri})"
        )
        if track.thumb:
            embed.set_thumbnail(url=track.thumb)
        return embed

    async def teardown(self):
        await self.disconnect(force=False)


class PaginatorSource(menus.ListPageSource):
    def __init__(self, entries, ctx, *, per_page=8):
        super().__init__(entries, per_page=per_page)
        self.ctx = ctx

    async def format_page(self, menu: menus.Menu, page):
        embed = discord.Embed(title=f'Queue for {self.ctx.guild}', color=await self.ctx.determine_color())
        embed.description = '\n'.join(page)
        embed.set_footer(text=f"Page {menu.current_page+1}/{self.get_max_pages()}")
        return embed


class Music(commands.Cog):
    """
    Music commands for music.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_privileged(self, ctx: commands.Context):
        """
        Check whether is author is a mod or DJ.

        If they aren't then this will return false.
        """
        player: Player = ctx.voice_client
        return player.dj == ctx.author or ctx.author.guild_permissions.kick_members

    @commands.Cog.listener('on_wavelink_track_exception')
    async def on_player_stop(self, node: wavelink.Node, payload):
        player: Player = payload.player
        await player.context.send(f"Error:{node.identifier}: {payload.error}")

    @commands.Cog.listener('on_wavelink_track_end')
    async def track_end(self, player: Player, track: Track, reason):
        print("redaslkdj")
        await player.do_next()

    @commands.Cog.listener('on_wavelink_track_stuck')
    async def track_stuck(self, player: Player, track: Track, threshold):
        await player.do_next()

    @commands.Cog.listener("on_voice_state_update")
    async def vs_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        player: Player = member.guild.voice_client

        channel = player.channel

        def check(mem, bef, aft):
            return mem == member and bef.channel is None and aft.channel == channel

        if after.channel is None and len(channel.members) == 1 and member.guild.me in channel.members:
            try:
                await self.bot.wait_for('voice_state_update', timeout=10, check=check)
            except asyncio.TimeoutError:
                return await player.teardown()

        if member == player.dj and after.channel is None:
            for m in channel.members:
                if m.bot:
                    continue
                else:
                    player.dj = m
                    return

        elif after.channel == channel and player.dj not in channel.members:
            player.dj = member

    async def cog_check(self, ctx: AvimetryContext):
        """Cog wide check, which disallows commands in DMs."""
        if not ctx.guild:
            await ctx.send('Music commands are not available in Private Messages.')
            return False

        return True

    async def cog_beforeasdjkl_invoke(self, ctx: AvimetryContext):
        """
        Check whether the author is inside the player's bound channel.
        """
        player: Player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, context=ctx)

        if player.context and player.context.channel != ctx.channel:
            await ctx.send(f'{ctx.author.display_name}, you need to use this in {player.context.channel.mention}.')

        if ctx.command.name == 'connect' and not player.context:
            return
        if not player.channel_id:
            return

        channel = self.bot.get_channel(int(player.channel_id))
        if not channel:
            return

        if player.is_connected and ctx.author not in channel.members:
            await ctx.send(f'{ctx.author.display_name}, you need to be in {channel.mention} to use this.')

    def required(self, ctx: AvimetryContext):
        """Method which returns required votes based on amount of members in a channel."""
        player: Player = ctx.voice_client
        channel = player.channel
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == 'stop' and len(channel.members) == 3:
            required = 2

        return required

    @core.command(aliases=["join"])
    async def connect(self, ctx: AvimetryContext):
        """Connect to a voice channel."""
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send("You need to be in a channel to use this command.")

        player = Player(context=ctx)
        voice_client = await channel.connect(cls=player)
        await ctx.send(f"Joined {voice_client.channel.mention}.")
        return voice_client

    @core.command(aliases=['stop', 'leave', 'fuckoff'])
    async def disconnect(self, ctx: AvimetryContext):
        """
        Stop the player and leave the channel.

        If you are the DJ or mod, It will always leave.
        If you are not, your vote will be added.
        """
        player: Player = ctx.voice_client

        if not player.is_connected():
            return

        if self.is_privileged(ctx):
            await ctx.send('Goodbye! :wave:')
            return await player.teardown()

        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if len(player.stop_votes) >= required:
            await ctx.send('Vote to stop passed. Goodbye! :wave:')
            await player.teardown()
        else:
            await ctx.send(f'{ctx.author.display_name} has voted to stop the player.')

    @core.command(aliases=["enqueue", "p"])
    async def play(self, ctx: AvimetryContext, *, query: wavelink.YouTubeTrack):
        """Play or queue a song with the given query."""
        player: Player = ctx.voice_client

        if not player:
            player = await ctx.invoke(self.connect)
        if player.is_paused():
            await ctx.invoke(self.resume)
        if not player.channel:
            print("no channel")
            return

        tracks = query

        if isinstance(tracks, wavelink.YouTubePlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author, thumb=track.thumb)
                await player.queue.put(track)

            embed = discord.Embed(
                title="Enqueued playlist",
                description=(
                    f"Playlist {tracks.name} with {len(tracks.tracks)} tracks added to the queue."
                )
            )
            if track.thumb:
                embed.set_thumbnail(url=tracks[0].thumb)
            await ctx.send(embed=embed)
        else:
            track = Track(tracks.id, tracks.info, requester=ctx.author, thumb=tracks.thumb)
            await ctx.send(embed=await player.build_added(track))
            await player.queue.put(track)
            print(player.queue)

        if not player.is_playing():
            print(player)
            print(player.is_playing())
            await player.do_next()
            print("p")

    @core.command(aliases=["ptop"])
    async def playtop(self, ctx: AvimetryContext, *, query: str):
        """
        Adds a song to the top of the queue.
        """
        player: Player = ctx.voice_client

        if not player:
            player = await ctx.invoke(self.connect)
        if player.is_paused():
            await ctx.invoke(self.resume)
        if not player.channel:
            return

        if self.is_privileged(ctx):
            query = query.strip('<>')
            if not URL_REG.match(query):
                query = f'ytsearch:{query}'

            tracks = await self.bot.wavelink.get_tracks(query)
            if not tracks:
                return await ctx.send('No songs found. Please try again.')

            if isinstance(tracks, wavelink.TrackPlaylist):
                return await ctx.send("Can't add a playlist to the top.")
            else:
                track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
                await ctx.send(f"Enqueued {track.title} to the top of the queue.")
                await player.queue.put(track, left=True)

            if not player.is_playing:
                await player.do_next()
        else:
            await ctx.send("Only the DJ can add songs to the top of the queue.")

    @core.command()
    async def pause(self, ctx: AvimetryContext):
        """
        Pause the currently playing song.

        If you are the DJ or mod, It will always pause.
        If you are not, your vote will be added.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send(f':pause_button: {ctx.author.display_name} has paused the player.')
            player.pause_votes.clear()
            return await player.set_pause(True)

        required = self.required(ctx)
        player.pause_votes.add(ctx.author)

        if len(player.pause_votes) >= required:
            await ctx.send(':pause_button: Pausing because vote to pause passed.')
            player.pause_votes.clear()
            await player.set_pause(True)
        else:
            await ctx.send(f'{ctx.author.display_name} has voted to pause the player.')

    @core.command()
    async def resume(self, ctx: AvimetryContext):
        """
        Resume the currently playing song.

        If you are the DJ or mod, It will always play.
        If you are not, your vote will be added.
        """
        player: Player = ctx.voice_client

        if not player.is_paused() or not player.is_connected():
            return

        if self.is_privileged(ctx):
            await ctx.send(f':arrow_forward: {ctx.author.display_name} has resumed the player.')
            player.resume_votes.clear()

            return await player.set_pause(False)

        required = self.required(ctx)
        player.resume_votes.add(ctx.author)

        if len(player.resume_votes) >= required:
            await ctx.send(':arrow_forward: Resuming because vote to resume passed.')
            player.resume_votes.clear()
            await player.set_pause(False)
        else:
            await ctx.send(f'{ctx.author.display_name} has voted to resume the player.')

    @core.command()
    async def skip(self, ctx: AvimetryContext):
        """
        Skip the current playing song.

        If you are the DJ or mod, It will always skip.
        If you are not, your vote will be added.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send(f':track_next: {ctx.author.display_name} has skipped the song.')
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            await ctx.send(':track_next: The song requester has skipped the song.')
            player.skip_votes.clear()

            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.send(':track_next: Skipping because vote to skip passed')
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.send(f'{ctx.author.display_name} voted to skip. {len(player.skip_votes)}/{required}')

    @core.command(aliases=["ff", "fastf", "fforward"])
    async def fastforward(self, ctx: AvimetryContext, seconds: int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        if not player.is_connected:
            return
        if self.is_privileged(ctx):
            await player.seek(player.position+seconds*1000)
            return await ctx.send(f":fast_forward: Fast forwarded {seconds} seconds")
        await ctx.send("Only the DJ can fast forward.")

    @core.command(aliases=["rw"])
    async def rewind(self, ctx: AvimetryContext, seconds: int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        if not player.is_connected:
            return
        if self.is_privileged(ctx):
            await player.seek(player.position-seconds*1000)
            return await ctx.send(f":rewind: Rewinded {seconds} seconds")
        await ctx.send("Only the DJ can rewind.")

    @core.command(aliases=["sk"])
    async def seek(self, ctx: AvimetryContext, seconds: int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        if not player.is_connected:
            return
        if self.is_privileged(ctx):
            await player.seek(seconds*1000)
            return await ctx.send(f"Set track position to {seconds} seconds")
        await ctx.send("Only the DJ can seek.")

    @core.command(aliases=['v', 'vol'])
    async def volume(self, ctx: AvimetryContext, *, vol: int):
        """
        Change the player's volume.

        You must be a DJ or mod to change the volume.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.send('Only the DJ or admins may change the volume.')

        if not 0 < vol < 101:
            return await ctx.send('Please enter a value between 1 and 100.')

        await player.set_volume(vol)
        await ctx.send(f':sound: Set the volume to {vol}%')

    @core.command(aliases=['mix'])
    async def shuffle(self, ctx: AvimetryContext):
        """
        Shuffles the queue.

        If you are the DJ or mod, It will shuffle the queue.
        If you are not, your vote will be added.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send(f':twisted_rightwards_arrows: {ctx.author.display_name} shuffled the queue.')
            player.shuffle_votes.clear()
            return random.shuffle(player.queue._queue)

        if player.queue.size < 3:
            return await ctx.send('Add more songs to the queue before shuffling.', delete_after=15)

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            await ctx.send(':twisted_rightwards_arrows: Shuffling queue because vote to shuffle passed.')
            player.shuffle_votes.clear()
            random.shuffle(player.queue._queue)
        else:
            await ctx.send(f'{ctx.author.display_name} has voted to shuffle the playlist.', delete_after=15)

    @core.command(aliases=['eq'])
    async def equalizer(self, ctx: AvimetryContext, *, equalizer: str):
        """Change the players equalizer."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.send('Only the DJ or admins may change the equalizer.')

        eqs = {'flat': wavelink.Equalizer.flat(),
               'boost': wavelink.Equalizer.boost(),
               'metal': wavelink.Equalizer.metal(),
               'piano': wavelink.Equalizer.piano()}

        eq = eqs.get(equalizer.lower())

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.send(f'Invalid EQ provided. Valid EQs:\n{joined}')

        await ctx.send(f'Successfully changed equalizer to {equalizer}')
        await player.set_eq(eq)

    @core.command(aliases=['q', 'upnext', 'next'])
    async def queue(self, ctx: AvimetryContext):
        """Display the players queued songs."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if player.queue.size == 0:
            return await ctx.send(f'The queue is empty. Use {ctx.prefix}play to add some songs!')

        entries = [f"`{index+1})` [{track.title}]({track.uri})" for index, track in enumerate(player.queue._queue)]
        pages = PaginatorSource(entries=entries, ctx=ctx)
        paginator = AvimetryPages(source=pages, timeout=120)

        await paginator.start(ctx)

    @core.command(aliases=["clq", "clqueue", "cqueue"])
    async def clearqueue(self, ctx: AvimetryContext):
        """
        Clears the player's queue.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return
        if player.queue.size == 0:
            return await ctx.send("The queue is empty. You can't clear an empty queue.")

        if self.is_privileged(ctx):
            await ctx.send("Cleared the queue.")
            return player.queue.clear()

        await ctx.send("Only the DJ can clear the queue.")

    @core.command(aliases=['np', 'now_playing', 'current'])
    async def nowplaying(self, ctx: AvimetryContext):
        """
        Show the currenly playing song.
        """
        player: Player = ctx.voice_client

        if not player:
            return
        pos = player.position
        await ctx.send(embed=await player.build_now_playing(position=pos))

    @core.command(aliases=['swap', 'new_dj'])
    async def swap_dj(self, ctx: AvimetryContext, *, member: discord.Member = None):
        """Swap the current DJ to another member in the voice channel."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.send('Only admins and the DJ may use this command.')

        members = self.bot.get_channel(int(player.channel_id)).members

        if member and member not in members:
            return await ctx.send(f'{member} is not currently in voice, so can not be a DJ.')

        if member and member == player.dj:
            return await ctx.send('Cannot swap DJ to the current DJ... :)')

        if len(members) <= 2:
            return await ctx.send('No more members to swap to.')

        if member:
            player.dj = member
            return await ctx.send(f'{member.mention} is now the DJ.')

        for m in members:
            if m == player.dj or m.bot:
                continue
            else:
                player.dj = m
                return await ctx.send(f'{member.mention} is now the DJ.')


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
