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

import datetime
import math
import random


from typing import Union

import discord
import wavelink
from discord.ext import commands

import core
from utils import (
    AvimetryBot,
    AvimetryContext,
    AvimetryPages,
    format_seconds
)
from .exceptions import NotInVoice
from .music import Player, Track, IsResponding, SearchView, SearchSelect, PaginatorSource


def in_voice():
    def predicate(ctx):
        if ctx.author.voice:
            return True
        raise NotInVoice

    return commands.check(predicate)


def in_correct_channel():
    def predicate(ctx: AvimetryContext):
        vc: Player = ctx.voice_client
        if not vc:
            raise NotInVoice
        if ctx.channel == vc.channel:
            return True
        raise NotInVoice
    return commands.check(predicate)


def convert_time(time: Union[int, str]):
    try:
        time = int(time)
    except ValueError:
        pass
    if isinstance(time, int):
        return time
    if isinstance(time, str):
        try:
            time = datetime.datetime.strptime(time, "%M:%S")
            delta = time - datetime.datetime(1900, 1, 1)
            return delta.total_seconds()
        except ValueError as e:
            raise commands.BadArgument("Time must be in MM:SS format.") from e


class Music(core.Cog):
    """
    Music commands for music.
    """

    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.emoji = "\U0001f3b5"
        self.load_time = datetime.datetime.now(datetime.timezone.utc)

    @core.Cog.listener("on_wavelink_track_exception")
    async def track_exception(self, player: Player, track: Track, error):
        player: Player = player
        await player.context.send(f"Error on {track.title}: {error}")

    @core.Cog.listener("on_wavelink_track_end")
    async def track_end(self, player: Player, track: Track, reason):
        await player.do_next()

    @core.Cog.listener("on_wavelink_track_stuck")
    async def track_stuck(self, player: Player, track: Track, threshold):
        await player.context.send(f"Track {track.name} got stuck. Skipping.")
        await player.do_next()

    @core.Cog.listener("on_voice_state_update")
    async def vs_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        player: Player = member.guild.voice_client
        if not player:
            return

        if member == self.bot.user:
            if after.channel is None:
                await player.teardown()

        if member.bot:
            return

        channel = player.channel

        def check(mem, bef, aft):
            return mem == member and bef.channel is None and aft.channel == channel

        if (
            after.channel is None
            and len(channel.members) == 1
            and member.guild.me in channel.members
        ):
            try:
                await self.bot.wait_for("voice_state_update", timeout=10, check=check)
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

    def is_privileged(self, ctx: commands.Context):
        """
        Check whether is author is a mod or DJ.

        If they aren't then this will return false.
        """
        player: Player = ctx.voice_client
        return player.dj == ctx.author or ctx.author.guild_permissions.kick_members

    async def cog_command_error(self, ctx: AvimetryContext, error: commands.CommandError):
        ctx.locally_handled = True
        if isinstance(error, NotInVoice):
            return await ctx.send("You must be in a voice channel to use this command.")
        else:
            ctx.locally_handled = False

    def required(self, ctx: AvimetryContext):
        """Method which returns required votes based on amount of members in a channel."""
        player: Player = ctx.voice_client
        channel = player.channel
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == "stop" and len(channel.members) == 3:
            required = 2

        return required

    @core.command(aliases=["join"])
    @in_voice()
    async def connect(self, ctx: AvimetryContext):
        """Connect to a voice channel."""
        player: Player = ctx.voice_client
        channel = ctx.author.voice.channel
        if player:
            if player.channel == channel:
                return await ctx.send("Already in channel.")
            return await player.move_to(channel)

        player = Player(context=ctx)
        voice_client = await channel.connect(cls=player)
        await ctx.send(f"Joined {voice_client.channel.mention}, anouncing songs in {ctx.channel.mention}.")
        return voice_client

    @core.command(aliases=["stop", "leave", "fuckoff"])
    @in_voice()
    async def disconnect(self, ctx: AvimetryContext):
        """
        Stop the player and leave the channel.

        If you are the DJ or mod, It will always leave.
        If you are not, your vote will be added.
        """
        player: Player = ctx.voice_client

        if not player:
            return

        if self.is_privileged(ctx):
            await ctx.send("Goodbye! :wave:")
            return await player.teardown()

        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if len(player.stop_votes) >= required:
            await ctx.send("Goodbye! (Vote passed) :wave:")
            await player.teardown()
        else:
            await ctx.send(f"Voted to stop the player. ({len(player.stop_votes)}/{required}).")

    @core.command()
    @core.is_owner()
    async def tplay(self, ctx, query: wavelink.YouTubeTrack):
        player = ctx.voice_client
        await player.play(query)

    @core.command(aliases=["enqueue", "p"])
    @in_voice()
    async def play(self, ctx: AvimetryContext, *, query: str):
        """Play or queue a song with the given query."""
        player: Player = ctx.voice_client

        if not player:
            player = await ctx.invoke(self.connect)
        if player.is_paused():
            await ctx.invoke(self.resume)
        if not player.channel:
            return

        async with IsResponding("\U000025b6\U0000fe0f", ctx.message, self.bot):
            tracks = await player.get_tracks(query)

        if not tracks:
            return await ctx.send("Could not find anything. Try again.")

        if isinstance(tracks, wavelink.YouTubePlaylist):
            for track in tracks.tracks:
                track = Track(
                    track.id, track.info, requester=ctx.author, thumb=track.thumb
                )
                await player.queue.put(track)

            embed = discord.Embed(
                title="Enqueued playlist",
                description=(
                    f"Playlist {tracks.name} with {len(tracks.tracks)} tracks added to the queue."
                ),
            )
            if tracks.tracks[0].thumb:
                embed.set_thumbnail(url=tracks.tracks[0].thumb)
            await ctx.send(embed=embed)
        elif isinstance(tracks, list):
            for track in tracks:
                track = Track(
                    track.id, track.info, requester=ctx.author, thumb=track.thumb
                )
                await player.queue.put(track)
            embed = discord.Embed(
                title="Enqueued Spotify playlist",
                description=(
                    f"Spotify playlist with {len(tracks)} tracks added to the queue."
                ),
            )
            if tracks[0].thumb:
                embed.set_thumbnail(url=tracks[0].thumb)
            await ctx.send(embed=embed)
        else:
            track = Track(
                tracks.id, tracks.info, requester=ctx.author, thumb=tracks.thumb
            )
            await ctx.send(embed=await player.build_added(track))
            await player.queue.put(track)

        if not player.is_playing():
            await player.do_next()

    @core.command()
    @in_voice()
    async def loop(self, ctx: AvimetryContext):
        """
        Loops the currently playing song.

        Use this command again to disable loop.
        """
        player: Player = ctx.voice_client

        if not player:
            return await ctx.send("I need to be in a voice channel.")
        if not player.track:
            return await ctx.send("There is no song playing to loop.")
        if player.loop_song:
            player.loop_song = None
            return await ctx.send(f"No longer looping: {player.track.title}")
        player.loop_song = player.track
        await ctx.send(f"Now looping: {player.track.title}")

    @core.command()
    @in_voice()
    @core.is_owner()
    async def search(self, ctx: AvimetryContext, *, query: str):
        """
        Search for a song on youtube and play it.
        """
        player: Player = ctx.voice_client
        if not player:
            return await ctx.send("I am not in a voice channel.")
        tracks = await player.get_tracks(query, bulk=True)
        if tracks:
            view = SearchView(ctx=ctx)
            view.add_item(SearchSelect(options=tracks))
            await ctx.send(f"Found {len(tracks)}. Please Select ", view=view)
            await view.wait()
            await ctx.invoke(self.play, query=view.option[0].title)

    @core.command(aliases=["ptop"])
    @in_voice()
    async def playtop(self, ctx: AvimetryContext, *, query: wavelink.YouTubeTrack):
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

        tracks = query
        if self.is_privileged(ctx):

            if isinstance(tracks, wavelink.YouTubePlaylist):
                for track in tracks.tracks:
                    track = Track(
                        track.id, track.info, requester=ctx.author, thumb=track.thumb
                    )
                    await player.queue.put(track, left=True)

                embed = discord.Embed(
                    title="Enqueued playlist",
                    description=(
                        f"Playlist {tracks.name} with {len(tracks.tracks)} tracks added to the queue."
                    ),
                )
                if track.thumb:
                    embed.set_thumbnail(url=tracks[0].thumb)
                await ctx.send(embed=embed)
            else:
                track = Track(
                    tracks.id, tracks.info, requester=ctx.author, thumb=tracks.thumb
                )
                await ctx.send(embed=await player.build_added(track))
                await player.queue.put(track)

            if not player.is_playing():
                await player.do_next()
        else:
            await ctx.send("Only the DJ can add songs to the top of the playlist.")

    @core.command()
    @in_voice()
    async def pause(self, ctx: AvimetryContext):
        """
        Pause the currently playing song.

        If you are the DJ or mod, It will always pause.
        If you are not, your vote will be added.
        """
        player: Player = ctx.voice_client

        if not player:
            return
        if not player.is_playing():
            return

        if self.is_privileged(ctx):
            await ctx.send(
                f":pause_button: {ctx.author.display_name} has paused the player."
            )
            player.pause_votes.clear()
            return await player.pause()

        required = self.required(ctx)
        player.pause_votes.add(ctx.author)

        if len(player.pause_votes) >= required:
            await ctx.send(":pause_button: Pausing because vote to pause passed.")
            player.pause_votes.clear()
            await player.pause()
        else:
            await ctx.send(f"Voted to pause the player. ({len(player.skip_votes)}/{required})")

    @core.command(aliases=["unpause"])
    @in_voice()
    async def resume(self, ctx: AvimetryContext):
        """
        Resume the currently playing song.

        If you are the DJ or mod, It will always play.
        If you are not, your vote will be added.
        """
        player: Player = ctx.voice_client

        if not player:
            return
        if not player.is_playing():
            return

        if self.is_privileged(ctx):
            await ctx.send(
                f":arrow_forward: {ctx.author.display_name} has resumed the player."
            )
            player.resume_votes.clear()

            return await player.resume()

        required = self.required(ctx)
        player.resume_votes.add(ctx.author)

        if len(player.resume_votes) >= required:
            await ctx.send(":arrow_forward: Resuming because vote to resume passed.")
            player.resume_votes.clear()
            await player.resume()
        else:
            await ctx.send(f"Voted to resume the player. ({len(player.skip_votes)}/{required})")

    @core.command()
    @in_voice()
    async def skip(self, ctx: AvimetryContext):
        """
        Skip the current playing song.

        If you are the DJ or mod, It will always skip.
        If you are not, your vote to skip will be added.
        """
        player: Player = ctx.voice_client

        if not player:
            return

        if self.is_privileged(ctx):
            await ctx.send(
                f":track_next: {ctx.author.display_name} has skipped the song."
            )
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            await ctx.send(":track_next: The song requester has skipped the song.")
            player.skip_votes.clear()

            return await player.stop()

        required = self.required(ctx)
        player.skip_votes.add(ctx.author)

        if len(player.skip_votes) >= required:
            await ctx.send(":track_next: Skipping because vote to skip passed")
            player.skip_votes.clear()
            await player.stop()
        else:
            await ctx.send(f"Voted to skip. ({len(player.skip_votes)}/{required})")

    @core.command(aliases=["ff", "fastf", "fforward"])
    @in_voice()
    async def fastforward(self, ctx: AvimetryContext, seconds: convert_time):
        """
        Fast forward an amount of seconds in the current song.

        Only the DJ can use this command.
        """
        player: Player = ctx.voice_client
        if not player:
            return
        if self.is_privileged(ctx):
            await player.seek((player.position + seconds) * 1000)
            pos = f"{format_seconds(player.position)}/{format_seconds(player.source.length)}"
            return await ctx.send(f":fast_forward: Fast forwarded {seconds} seconds. ({pos})")
        await ctx.send("Only the DJ can fast forward.")

    @core.command(aliases=["rw"])
    @in_voice()
    async def rewind(self, ctx: AvimetryContext, seconds: convert_time):
        """
        Rewind a certain amount of seconds in the current song.

        Only the DJ can use this command.
        """
        player: Player = ctx.voice_client
        if not player:
            return
        if self.is_privileged(ctx):
            await player.seek((player.position - seconds) * 1000)
            pos = f"{format_seconds(player.position)}/{format_seconds(player.source.length)}"
            return await ctx.send(f":rewind: Rewinded {seconds} seconds. ({pos})")
        await ctx.send("Only the DJ can rewind.")

    @core.command(aliases=["sk"])
    @in_voice()
    async def seek(self, ctx: AvimetryContext, seconds: convert_time):
        """
        Seek in the cuuent song.

        Entering an amount lower than 0 will restart the song.
        """
        player: Player = ctx.voice_client
        if not player:
            return
        if self.is_privileged(ctx):
            if seconds > player.source.length:
                return await ctx.send("That is longer than the song!")
            await ctx.send(f"Seeked to {format_seconds(seconds)}/{format_seconds(player.source.length)}")
            return await player.seek(seconds * 1000)
        await ctx.send("Only the DJ can seek.")

    @core.command(aliases=["v", "vol"])
    @in_voice()
    async def volume(self, ctx: AvimetryContext, *, vol: int):
        """
        Change the player's volume.

        You must be a DJ or mod to change the volume.
        """
        player: Player = ctx.voice_client

        if not player:
            return

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the volume.")

        if not 0 < vol < 101:
            return await ctx.send("Please enter a value between 1 and 100.")

        await player.set_volume(vol)
        await ctx.send(f":sound: Set the volume to {vol}%")

    @core.command(aliases=["mix"])
    @in_voice()
    async def shuffle(self, ctx: AvimetryContext):
        """
        Shuffles the queue.

        If you are the DJ or mod, It will shuffle the queue.
        If you are not, your vote will be added.
        """
        player: Player = ctx.voice_client

        if not player:
            return

        if self.is_privileged(ctx):
            await ctx.send(
                f":twisted_rightwards_arrows: {ctx.author.display_name} shuffled the queue."
            )
            player.shuffle_votes.clear()
            return random.shuffle(player.queue._queue)

        if player.queue.size < 3:
            return await ctx.send(
                "Add more songs to the queue before shuffling.", delete_after=15
            )

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            await ctx.send(
                ":twisted_rightwards_arrows: Shuffling queue because vote to shuffle passed."
            )
            player.shuffle_votes.clear()
            random.shuffle(player.queue._queue)
        else:
            await ctx.send(
                f"Voted to shuffle the playlist. ({len(player.shuffle_votes)}/{required})",
            )

    @core.command()
    @in_voice()
    async def announce(self, ctx: AvimetryContext, toggle: bool):
        """
        Whether to announce the song.

        This will reset every time the bot joins a voice channel.
        """
        player: Player = ctx.voice_client
        player.announce = toggle
        if toggle:
            return await ctx.send("Songs will be announced.")
        return await ctx.send("Song will no longer be announced.")

    @core.command()
    @in_voice()
    async def duplicated(self, ctx: AvimetryContext, toggle: bool):
        """
        Whether to allow duplicated in the queue.

        This will reset every time the bot joins a voice channel.
        """
        player: Player = ctx.voice_client
        player.allow_duplicates = toggle
        if toggle:
            return await ctx.send("Duplicate songs are now allowed.")
        return await ctx.send("Duplicate songs are no longer allowed in the queue.")

    @core.command(aliases=["eq"], enabled=False)
    @in_voice()
    async def equalizer(self, ctx: AvimetryContext, *, equalizer: str):
        """Change the players equalizer."""
        player: Player = ctx.voice_client

        if not player:
            return

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the equalizer.")

        eqs = {
            "flat": wavelink.Equalizer.flat(),
            "boost": wavelink.Equalizer.boost(),
            "metal": wavelink.Equalizer.metal(),
            "piano": wavelink.Equalizer.piano(),
        }

        eq = eqs.get(equalizer.lower())

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.send(f"Invalid EQ provided. Valid EQs:\n{joined}")

        await ctx.send(f"Successfully changed equalizer to {equalizer}")
        await player.set_eq(eq)

    @core.command(aliases=["q", "upnext"])
    @in_voice()
    async def queue(self, ctx: AvimetryContext):
        """Display the players queued songs."""
        player: Player = ctx.voice_client

        if not player:
            return

        if player.queue.size == 0:
            return await ctx.send(
                f"The queue is empty. Use {ctx.prefix}play to add some songs!"
            )

        entries = [
            f"`{index+1})` [{track.title}]({track.uri})"
            for index, track in enumerate(player.queue._queue)
        ]
        pages = PaginatorSource(entries=entries, ctx=ctx)
        paginator = AvimetryPages(
            source=pages, timeout=120, ctx=ctx, disable_view_after=True
        )
        await paginator.start()

    @core.command(aliases=["clq", "clqueue", "cqueue"])
    @in_voice()
    async def clearqueue(self, ctx: AvimetryContext):
        """
        Clears the player's queue.
        """
        player: Player = ctx.voice_client

        if not player:
            return
        if player.queue.size == 0:
            return await ctx.send("The queue is empty. You can't clear an empty queue.")

        if self.is_privileged(ctx):
            await ctx.send("Cleared the queue.")
            return player.queue.clear()

        await ctx.send("Only the DJ can clear the queue.")

    @core.command(aliases=["np", "now_playing", "current"])
    async def nowplaying(self, ctx: AvimetryContext):
        """
        Show the currenly playing song.
        """
        player: Player = ctx.voice_client

        if not player:
            return
        pos = player.position
        await ctx.send(embed=await player.build_now_playing(position=pos))

    @core.command(aliases=["swap", "new_dj"])
    @in_voice()
    async def swap_dj(self, ctx: AvimetryContext, *, member: discord.Member = None):
        """Swap the current DJ to another member in the voice channel."""
        player: Player = ctx.voice_client

        if not player:
            return

        if not self.is_privileged(ctx):
            return await ctx.send("Only admins and the DJ may use this command.")

        members = player.channel.members

        if member and member not in members:
            return await ctx.send(
                f"{member} is not currently in voice, so can not be a DJ."
            )

        if member and member == player.dj:
            return await ctx.send("Cannot swap DJ to the current DJ... :)")

        if len(members) <= 2:
            return await ctx.send("No more members to swap to.")

        if member:
            player.dj = member
            return await ctx.send(f"{member.mention} is now the DJ.")

        for m in members:
            if m == player.dj or m.bot:
                continue
            else:
                player.dj = m
                return await ctx.send(f"{member.mention} is now the DJ.")


def setup(bot: AvimetryBot):
    bot.add_cog(Music(bot))