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

    def add(self, track, append_left=False):
        if append_left:
            self._queue.appendleft(track)
        else:
            self._queue.append(track)

    def remove(self, track):
        self._queue.remove(track)

    def clear(self):
        self._queue.clear()

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

        self.requester = kwargs.get('requester')


class Player(wavelink.Player):
    """Custom wavelink Player class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.context: AvimetryContext = kwargs.get('context', None)
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
        if self.is_playing or self.waiting:
            return

        # Clear the votes for a new song...
        self.pause_votes.clear()
        self.resume_votes.clear()
        self.skip_votes.clear()
        self.shuffle_votes.clear()
        self.stop_votes.clear()

        try:
            self.waiting = True
            with async_timeout.timeout(300):
                track = await self.queue.get()
        except asyncio.TimeoutError:
            return await self.teardown()

        await self.play(track)
        self.waiting = False

        await self.context.channel.send(embed=await self.build_embed())

    async def build_embed(self, position=None) -> typing.Optional[discord.Embed]:
        """
        Builds the "now playing" embed
        """
        track = self.current
        if not track:
            return

        channel = self.bot.get_channel(int(self.channel_id))

        embed = discord.Embed(title=f'Now Playing in {channel.guild.name}')
        if self.context:
            embed.color = await self.context.determine_color()
        time = f'Length: {format_seconds(track.length // 1000)}\n\n'
        if position:
            time = f'Position {format_seconds(position//1000)}/{format_seconds(track.length // 1000)}\n\n'
        embed.description = (
            f'Song: [{track.title}]({track.uri})\n\n'
            f'{time}'
            f"Requested by: {track.requester.mention} (`{track.requester}`)\n\n"
            f"Up next: {self.queue.up_next or 'Add more songs!'}"
        )
        embed.set_thumbnail(url=track.thumb)
        return embed

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass


class PaginatorSource(menus.ListPageSource):
    def __init__(self, entries, ctx, *, per_page=8):
        super().__init__(entries, per_page=per_page)
        self.ctx = ctx

    async def format_page(self, menu: menus.Menu, page):
        embed = discord.Embed(title=f'Queue for {self.ctx.guild}', color=await self.ctx.determine_color())
        embed.description = '\n'.join(page)
        embed.set_footer(text=f"Page {menu.current_page+1}/{self.get_max_pages()}")
        return embed


class Music(commands.Cog, wavelink.WavelinkMixin):
    """Music Cog."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_privileged(self, ctx: commands.Context):
        """
        Check whether is author is a mod or DJ.

        If they aren't then this will return false.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        return player.dj == ctx.author or ctx.author.guild_permissions.kick_members

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node: wavelink.Node):
        print(f'Node {node.identifier} is ready!')

    @wavelink.WavelinkMixin.listener('on_track_stuck')
    @wavelink.WavelinkMixin.listener('on_track_end')
    @wavelink.WavelinkMixin.listener('on_track_exception')
    async def on_player_stop(self, node: wavelink.Node, payload):
        await payload.player.do_next()

    @commands.Cog.listener("on_voice_state_update")
    async def vs_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        player: Player = self.bot.wavelink.get_player(member.guild.id, cls=Player)

        if not player.channel_id or not player.context:
            player.node.players.pop(member.guild.id)
            return

        channel = self.bot.get_channel(int(player.channel_id))

        if after.channel is None and not channel.members:
            await player.teardown()

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

    async def cog_before_invoke(self, ctx: AvimetryContext):
        """
        Check whether the author is inside the player's bound channel.
        """
        player: Player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, context=ctx)

        if player.context and player.context.channel != ctx.channel:
            await ctx.send(f'{ctx.author.mention}, You need to use this in {player.context.channel.mention}.')

        if ctx.command.name == 'connect' and not player.context:
            return
        if not player.channel_id:
            return

        channel = self.bot.get_channel(int(player.channel_id))
        if not channel:
            return

        if player.is_connected and ctx.author not in channel.members:
            await ctx.send(f'{ctx.author.mention}, You need to be in {channel.mention} to use this.')

    def required(self, ctx: AvimetryContext):
        """Method which returns required votes based on amount of members in a channel."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        channel = self.bot.get_channel(int(player.channel_id))
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == 'stop' and len(channel.members) == 3:
            required = 2

        return required

    @core.command(aliases=["join"])
    async def connect(self, ctx: AvimetryContext):
        """Connect to a voice channel."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if player.is_connected and ctx.author.voice:
            channel = ctx.author.voice.channel
            message = f"Moved to {channel.mention}"

        elif ctx.author.voice:
            channel = ctx.author.voice.channel
            message = f"Joined {channel.mention}"
        else:
            return await ctx.send("You need to be in a channel to use this.")

        await player.connect(channel.id)
        await ctx.send(message)

    @core.command(aliases=["enqueue", "p"])
    async def play(self, ctx: AvimetryContext, *, query: str):
        """Play or queue a song with the given query."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            await ctx.invoke(self.connect)
        if player.is_paused:
            await ctx.invoke(self.resume)
        if not player.channel_id:
            return

        query = query.strip('<>')
        if not URL_REG.match(query):
            query = f'ytsearch:{query}'

        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            return await ctx.send('No songs were found with that query. Please try again.', delete_after=15)

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                player.queue.add(track)

            await ctx.send(f"Enqueued {tracks.data['playlistInfo']['name']} ({len(tracks.tracks)} tracks)")
        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            await ctx.send(f"Enqueued {track.title}.")
            player.queue.add(track)

        if not player.is_playing:
            await player.do_next()

    @core.command(aliases=["ptop"])
    async def playtop(self, ctx: AvimetryContext, *, query: str):
        """
        Adds a song to the top of the queue.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            await ctx.invoke(self.connect)
        if player.is_paused:
            await ctx.invoke(self.resume)
        if not player.channel_id:
            return

        if self.is_privileged(ctx):
            query = query.strip('<>')
            if not URL_REG.match(query):
                query = f'ytsearch:{query}'

            tracks = await self.bot.wavelink.get_tracks(query)
            if not tracks:
                return await ctx.send('No songs found. Please try again.', delete_after=15)

            if isinstance(tracks, wavelink.TrackPlaylist):
                return await ctx.send("Can't add a playlist to the top.")
            else:
                track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
                await ctx.send(f"Enqueued {track.title} to the top of the queue.")
                player.queue.add(track, append_left=True)

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
            await ctx.send(f'{ctx.author.mention} has paused the player.', delete_after=10)
            player.pause_votes.clear()
            return await player.set_pause(True)

        required = self.required(ctx)
        player.pause_votes.add(ctx.author)

        if len(player.pause_votes) >= required:
            await ctx.send('Vote to pause passed. Pausing player.', delete_after=10)
            player.pause_votes.clear()
            await player.set_pause(True)
        else:
            await ctx.send(f'{ctx.author.mention} has voted to pause the player.', delete_after=15)

    @core.command()
    async def resume(self, ctx: AvimetryContext):
        """
        Resume the currently playing song.

        If you are the DJ or mod, It will always play.
        If you are not, your vote will be added.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send(f'{ctx.author.mention} has resumed the player.', delete_after=10)
            player.resume_votes.clear()

            return await player.set_pause(False)

        required = self.required(ctx)
        player.resume_votes.add(ctx.author)

        if len(player.resume_votes) >= required:
            await ctx.send('Vote to resume passed. Resuming player.', delete_after=10)
            player.resume_votes.clear()
            await player.set_pause(False)
        else:
            await ctx.send(f'{ctx.author.mention} has voted to resume the player.', delete_after=15)

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
            await ctx.send(f'{ctx.author.mention} has skipped the song.', delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            await ctx.send('The song requester has skipped the song.', delete_after=10)
            player.skip_votes.clear()

            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.send('Vote to skip passed. Skipping song.', delete_after=10)
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.send(f'{ctx.author.mention} voted to skip. {len(player.skip_votes)}/{required}', delete_after=15)

    @core.command(aliases=["ff", "fastf", "fforward"])
    async def fastforward(self, ctx: AvimetryContext, seconds: int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        if not player.is_connected:
            return
        if self.is_privileged(ctx):
            await player.seek(seconds*1000)
            return await ctx.send(f"Fast forwarded {seconds} seconds")
        await ctx.send("Only the DJ can fast forward.")

    @core.command(aliases=["rw"])
    async def rewind(self, ctx: AvimetryContext, seconds: int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        if not player.is_connected:
            return
        if self.is_privileged(ctx):
            await player.seek(player.position-seconds*1000)
            return await ctx.send(f"Went back {seconds} seconds")
        await ctx.send("Only the DJ can rewind.")

    @core.command(aliases=["sk"])
    async def seek(self, ctx: AvimetryContext, seconds: int):
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)
        if not player.is_connected:
            return
        if self.is_privileged(ctx):
            await player.seek(player.position+seconds*1000)
            return await ctx.send(f"Set track position to {seconds} seconds")
        await ctx.send("Only the DJ can seek.")

    @core.command(aliases=['disconnect', 'leave', 'fuckoff'])
    async def stop(self, ctx: AvimetryContext):
        """
        Stop the player and leave the channel.

        If you are the DJ or mod, It will always leave.
        If you are not, your vote will be added.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send('Goodbye! :wave:', delete_after=10)
            return await player.teardown()

        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if len(player.stop_votes) >= required:
            await ctx.send('Vote to stop passed. Goodbye! :wave:', delete_after=10)
            await player.teardown()
        else:
            await ctx.send(f'{ctx.author.mention} has voted to stop the player.', delete_after=15)

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
        await ctx.send(f'Set the volume to **{vol}**%', delete_after=7)

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
            await ctx.send(f'{ctx.author.mention} has shuffled the queue.', delete_after=10)
            player.shuffle_votes.clear()
            return random.shuffle(player.queue._queue)

        if player.queue.size < 3:
            return await ctx.send('Add more songs to the queue before shuffling.', delete_after=15)

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            await ctx.send('Vote to shuffle passed. Shuffling the playlist.', delete_after=10)
            player.shuffle_votes.clear()
            random.shuffle(player.queue._queue)
        else:
            await ctx.send(f'{ctx.author.mention} has voted to shuffle the playlist.', delete_after=15)

    @core.command(hidden=True)
    async def vol_up(self, ctx: AvimetryContext):
        """Command used for volume up button."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected or not self.is_privileged(ctx):
            return

        vol = int(math.ceil((player.volume + 10) / 10)) * 10

        if vol > 100:
            vol = 100
            await ctx.send('Maximum volume reached', delete_after=7)

        await player.set_volume(vol)

    @core.command(hidden=True)
    async def vol_down(self, ctx: AvimetryContext):
        """Command used for volume down button."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected or not self.is_privileged(ctx):
            return

        vol = int(math.ceil((player.volume - 10) / 10)) * 10

        if vol < 0:
            vol = 0
            await ctx.send('Player is currently muted', delete_after=10)

        await player.set_volume(vol)

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

        await ctx.send(f'Successfully changed equalizer to {equalizer}', delete_after=15)
        await player.set_eq(eq)

    @core.command(aliases=['q', 'upnext', 'next'])
    async def queue(self, ctx: AvimetryContext):
        """Display the players queued songs."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if player.queue.size == 0:
            return await ctx.send(f'The queue is empty. Use {ctx.prefix}play to add some songs!', delete_after=15)

        entries = [f"`{index+1})` [{track.title}]({track.uri})" for index, track in enumerate(player.queue._queue)]
        pages = PaginatorSource(entries=entries, ctx=ctx)
        paginator = AvimetryPages(source=pages, timeout=120)

        await paginator.start(ctx)

    @core.command(aliases=['np', 'now_playing', 'current'])
    async def nowplaying(self, ctx: AvimetryContext):
        """
        Show the currenly playing song.
        """
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return
        pos = player.position
        await ctx.send(embed=await player.build_embed(position=pos))

    @core.command(aliases=['swap', 'new_dj'])
    async def swap_dj(self, ctx: AvimetryContext, *, member: discord.Member = None):
        """Swap the current DJ to another member in the voice channel."""
        player: Player = self.bot.wavelink.get_player(guild_id=ctx.guild.id, cls=Player, context=ctx)

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.send('Only admins and the DJ may use this command.', delete_after=15)

        members = self.bot.get_channel(int(player.channel_id)).members

        if member and member not in members:
            return await ctx.send(f'{member} is not currently in voice, so can not be a DJ.', delete_after=15)

        if member and member == player.dj:
            return await ctx.send('Cannot swap DJ to the current DJ... :)', delete_after=15)

        if len(members) <= 2:
            return await ctx.send('No more members to swap to.', delete_after=15)

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
