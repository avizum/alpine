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
import datetime as dt
import math
import random
from typing import Literal, TYPE_CHECKING

import discord
import wavelink
from discord.ext import commands
from wavelink.ext import spotify

import core
from utils import format_seconds, Paginator

from .exceptions import BotNotInVoice, IncorrectChannelError, NotInVoice
from .music import EventPayload, PaginatorSource, Player, Track

if TYPE_CHECKING:
    from datetime import datetime

    from core import Bot, Context


class ConvertTime(commands.Converter, int):
    @classmethod
    def convert_time(cls, ctx: Context, argument: int | str) -> int:
        try:
            argument = int(argument)
        except ValueError:
            pass
        if isinstance(argument, int):
            return argument
        if isinstance(argument, str):
            try:
                time_ = dt.datetime.strptime(argument, "%M:%S")
                delta = time_ - dt.datetime(1900, 1, 1)
                return int(delta.total_seconds())
            except ValueError as e:
                raise commands.BadArgument("Time must be in MM:SS format.") from e


class Music(core.Cog):
    """
    Music commands for music.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.emoji: str = "\U0001f3b5"
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)

    async def cog_check(self, ctx: Context) -> bool:
        try:
            wavelink.NodePool.get_node()
        except wavelink.InvalidNode as e:
            raise NotInVoice("No nodes are connected. Try again later.") from e
        return True

    @staticmethod
    def in_voice():
        def predicate(ctx: Context):
            player: Player = ctx.voice_client
            if not ctx.author.voice:
                raise NotInVoice("You are not in a voice channel.")
            if not player:
                return True
            elif player.channel and player.channel != ctx.author.voice.channel:
                raise IncorrectChannelError(f"This command can only be used in {player.channel.mention}.")
            return True

        return commands.check(predicate)

    @staticmethod
    def bot_in_voice():
        def predicate(ctx: Context):
            player: Player = ctx.voice_client
            if player:
                return True
            raise BotNotInVoice("I am not in a voice channel.")

        return commands.check(predicate)

    @staticmethod
    def in_bound_channel():
        def predicate(ctx: Context):
            if ctx.voice_client is None:
                return True
            if ctx.voice_client and ctx.channel == ctx.voice_client.bound:
                return True
            raise IncorrectChannelError(f"This command can only be used in {ctx.voice_client.bound.mention}.")

        return commands.check(predicate)

    @core.Cog.listener("on_wavelink_track_exception")
    async def track_exception(self, payload: EventPayload):
        player = payload.player
        track = payload.track
        await player.context.channel.send(f"Error on {track.title}: {payload.reason}")

    @core.Cog.listener("on_wavelink_track_end")
    async def track_end(self, payload: EventPayload):
        player = payload.player
        await player.do_next()

    @core.Cog.listener("on_wavelink_track_stuck")
    async def track_stuck(self, payload: EventPayload):
        player = payload.player
        track = payload.track
        await player.context.channel.send(f"Track {track.title} got stuck. Skipping.")
        await player.do_next()

    @core.Cog.listener("on_voice_state_update")
    async def vs_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.guild.voice_client is None:
            return
        player: Player = member.guild.voice_client  # type: ignore

        if member == self.bot.user:
            if after.channel is None:
                await player.disconnect()

        if member.bot:
            return

        channel = player.channel

        def check(mem, bef, aft):
            return mem == member and aft.channel == channel

        if after.channel is None and len(channel.members) == 1 and member.guild.me in channel.members:
            try:
                await self.bot.wait_for("voice_state_update", timeout=30, check=check)
            except asyncio.TimeoutError:
                if player.context:
                    await player.context.send("Disconnecting since everyone left the channel.")
                return await player.disconnect()

        if member == player.dj and after.channel is None:
            for m in channel.members:
                if m.bot:
                    continue
                else:
                    player.dj = m
                    return

        elif after.channel == channel and player.dj not in channel.members:
            player.dj = member

    def is_privileged(self, ctx: Context):
        """
        Check whether is author is a mod or DJ.

        If they aren't then this will return false.
        """
        player: Player = ctx.voice_client
        return player.dj == ctx.author or ctx.author.guild_permissions.kick_members

    async def cog_command_error(self, ctx: Context, error: commands.CommandError):
        ctx.locally_handled = True
        if isinstance(error, (NotInVoice, BotNotInVoice, IncorrectChannelError)):
            return await ctx.send(str(error), ephemeral=True, delete_after=30)
        else:
            ctx.locally_handled = False

    def required(self, ctx: Context):
        """Method which returns required votes based on amount of members in a channel."""
        player: Player = ctx.voice_client
        channel = player.channel
        required = math.ceil((len(channel.members) - 1) / 2.5)

        if ctx.command.name == "stop" and len(channel.members) == 3:
            required = 2

        return required

    async def do_connect(self, ctx: Context) -> Player | None:
        assert ctx.author.voice is not None
        player: Player = ctx.voice_client
        channel = ctx.author.voice.channel
        if channel is None:
            await ctx.send("You are not in a voice channel.")
            return
        if not channel.permissions_for(ctx.me).connect:
            await ctx.send("I do not have permission to connect to your channel.")
            return
        if player:
            if player.channel == channel:
                await ctx.send("Already in a voice channel.")
                return
            await player.move_to(channel)  # type: ignore
            return
        player = await channel.connect(cls=Player(context=ctx))  # type: ignore

        if isinstance(player.channel, discord.StageChannel):
            try:
                await ctx.me.edit(suppress=False)
            except discord.Forbidden:
                pass
        await ctx.send(f"Joined {player.channel.mention}, bound to {ctx.channel.mention}.")
        return player

    @core.command(hybrid=True, aliases=["join"])
    @in_voice()
    async def connect(self, ctx: Context):
        """Connect to a voice channel."""
        await self.do_connect(ctx)

    @core.command(hybrid=True, aliases=["leave", "fuckoff"])
    @in_voice()
    @in_bound_channel()
    async def disconnect(self, ctx: Context):
        """
        Stop the player and leave the channel.

        If you are the DJ or mod, It will always leave.
        If you are not, your vote will be added.
        """
        player: Player = ctx.voice_client

        if ctx.interaction and not player:
            return await ctx.send("Already disconnected.", ephemeral=True)

        if not player:
            return

        if self.is_privileged(ctx):
            await ctx.send("Goodbye! :wave:")
            return await player.disconnect()

        required = self.required(ctx)
        player.stop_votes.add(ctx.author)

        if len(player.stop_votes) >= required:
            await ctx.send("Goodbye! (Vote passed) :wave:")
            await player.disconnect()
        else:
            await ctx.send(f"Voted to stop the player. ({len(player.stop_votes)}/{required}).")

    @core.command(hybrid=True, aliases=["enqueue", "p"])
    @in_voice()
    @in_bound_channel()
    @core.describe(query="What to search for.")
    async def play(self, ctx: Context, *, query: str):
        """
        Play or queue a song with the given query.
        """
        player = ctx.voice_client
        if not player:
            player = await self.do_connect(ctx)
            if not isinstance(player, Player):
                return
        if not player.channel:
            return

        search = await player.get_tracks(query)
        if not search:
            return await ctx.send("No results found matching your query.")

        print(search)

        if isinstance(search, wavelink.YouTubeTrack):
            track = Track(track=search, context=ctx)
            player.queue.put(track)
            await ctx.send(embed=await player.build_added(track))

        if isinstance(search, wavelink.YouTubePlaylist):
            for track in search.tracks:
                track = Track(track=track, context=ctx)
                player.queue.put(track)

            embed = discord.Embed(
                title="Enqueued YouTube playlist",
                description=(f"Playlist {search.name} with {len(search.tracks)} tracks added to the queue."),
            )
            if search.tracks[0].thumb:
                embed.set_thumbnail(url=search.tracks[0].thumb)
            await ctx.send(embed=embed)

        elif isinstance(search, list) and isinstance(search[0], spotify.SpotifyTrack):
            for track in search:
                track = Track(track=track, context=ctx)
                player.queue.put(track)
            embed = discord.Embed(
                title="Enqueued Spotify playlist",
                description=(f"Spotify playlist with {len(search)} tracks added to the queue."),
            )
            await ctx.send(embed=embed)

        elif isinstance(query, spotify.SpotifyTrack):
            track = Track(track=query, context=ctx)
            player.queue.put(track)
            await ctx.send(embed=await player.build_added(track))

        if not player.is_playing():
            await player.do_next()

    @core.group(hybrid=True, name="loop", fallback="track")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def track_loop(self, ctx: Context):
        """
        Loops the currently playing song.

        This command toggles the looping of the track.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admin can use this command.")

        # Track will always have a title.
        if not player.track:
            return await ctx.send("There is no song playing to loop.")
        if player.loop_song:
            player.loop_song = None
            return await ctx.send(f"No longer looping: {player.track.title}")  # type: ignore
        player.loop_song = player.track
        await ctx.send(f"Now looping: {player.track.title}")  # type: ignore

    @track_loop.command(name="queue", enabled=False)
    @core.is_owner()
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def loop_queue(self, ctx: Context):
        """
        Loops the whole queue.

        This command toggles the looping of the queue.
        """
        player: Player = ctx.voice_client

        if not player:
            return await ctx.send()

    # @core.command(hybrid=True)
    # @in_voice()
    # @core.is_owner()
    # @core.describe(index="Song position in the queue to remove.")
    # async def remove(self, ctx: Context, index: int):
    #     """
    #     Removes a song from the queue.

    #     The index is the position of the song in the queue.
    #     """
    #     player: Player = ctx.voice_client
    #     if not player:
    #         return await ctx.send("I am not in a voice channel.")
    #     if not player.queue._queue:
    #         return await ctx.send("There are no songs in the queue.")
    #     try:
    #         await player.queue.remove_at_index(index)
    #     except IndexError:
    #         return await ctx.send("That is not a valid index.")
    #     await ctx.send("Removed song from queue.")

    @core.command(hybrid=True, aliases=["stop"])
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def pause(self, ctx: Context):
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
            await ctx.send(f":pause_button: {ctx.author.display_name} has paused the player.")
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

    @core.command(hybrid=True, aliases=["unpause"])
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def resume(self, ctx: Context):
        """
        Resume the currently playing song.

        If you are the DJ or mod, It will always play.
        If you are not, your vote will be added.
        """
        player: Player = ctx.voice_client

        if not player:
            return
        if not player.is_playing():
            return await ctx.send("Player is not playing anything.")

        if self.is_privileged(ctx):
            await ctx.send(f":arrow_forward: {ctx.author.display_name} has resumed the player.")
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

    @core.command(hybrid=True)
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def skip(self, ctx: Context):
        """
        Skip the current playing song.

        If you are the DJ or mod, It will always skip.
        If you are not, your vote to skip will be added.
        """
        player: Player = ctx.voice_client

        if not player:
            return

        if self.is_privileged(ctx):
            await ctx.send(f":track_next: {ctx.author.display_name} has skipped the song.")
            player.skip_votes.clear()

            return await player.stop()

        if ctx.author == player.track.requester:  # type: ignore  # Track should always have a requester.
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

    @core.command(hybrid=True, aliases=["ff", "fastf", "fforward"])
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(seconds="How many seconds to skip forward.")
    async def fastforward(self, ctx: Context, seconds: ConvertTime):
        """
        Fast forward an amount of seconds in the current song.

        Only the DJ can use this command.
        """
        player: Player = ctx.voice_client
        if not player:
            return await ctx.send("I am not in a voice channel.")
        if player.current is None:
            return await ctx.send("There is no song playing.")
        if self.is_privileged(ctx):
            await player.seek((int(player.position) + seconds) * 1000)
            pos = f"{format_seconds(player.position)}/{format_seconds(player.current.length)}"
            return await ctx.send(f":fast_forward: Fast forwarded {seconds} seconds. ({pos})")
        await ctx.send("Only the DJ can fast forward.")

    @core.command(hybrid=True, aliases=["rw"])
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(seconds="How many seconds to skip back.")
    async def rewind(self, ctx: Context, seconds: ConvertTime):
        """
        Rewind a certain amount of seconds in the current song.

        Only the DJ can use this command.
        """
        player: Player = ctx.voice_client
        if not player:
            return await ctx.send("I am not in a voice channel.")
        if player.current is None:
            return await ctx.send("There is no song playing.")
        if self.is_privileged(ctx):
            await player.seek((int(player.position) - seconds) * 1000)
            pos = f"{format_seconds(player.position)}/{format_seconds(player.current.length)}"
            return await ctx.send(f":rewind: Rewinded {seconds} seconds. ({pos})")
        await ctx.send("Only the DJ can rewind.")

    @core.command(hybrid=True, aliases=["sk"])
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(seconds="What time in the song to seek to.")
    async def seek(self, ctx: Context, seconds: ConvertTime):
        """
        Seek in the current song.

        Entering an amount lower than 0 will restart the song.
        """
        player: Player = ctx.voice_client
        if not player:
            return await ctx.send("I am not in a voice channel.")
        if player.current is None:
            return await ctx.send("There is no song playing.")
        if self.is_privileged(ctx):
            if seconds > player.current.length:
                return await ctx.send("That is longer than the song!")
            await ctx.send(f"Seeked to {format_seconds(seconds)}/{format_seconds(player.current.length)}")
            return await player.seek(seconds * 1000)
        await ctx.send("Only the DJ can seek.")

    @core.command(hybrid=True, aliases=["v", "vol"])
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(volume="What volume to set the player to.")
    async def volume(self, ctx: Context, *, volume: int):
        """
        Change the player's volume.

        You must be a DJ or mod to change the volume.
        """
        player: Player = ctx.voice_client

        if not player:
            return

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the volume.")

        if not 0 < volume < 201:
            return await ctx.send("Please enter a value between 1 and 100.")

        await player.set_volume(volume)
        await ctx.send(f":sound: Set the volume to {volume}%")

    @core.command(hybrid=True, aliases=["mix"])
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def shuffle(self, ctx: Context):
        """
        Shuffles the queue.

        If you are the DJ or mod, It will shuffle the queue.
        If you are not, your vote will be added.
        """
        player: Player = ctx.voice_client

        if not player:
            return

        if self.is_privileged(ctx):
            await ctx.send(f":twisted_rightwards_arrows: {ctx.author.display_name} shuffled the queue.")
            player.shuffle_votes.clear()
            return random.shuffle(player.queue._queue)

        if player.queue.size < 3:
            return await ctx.send("Add more songs to the queue before shuffling.", delete_after=15)

        required = self.required(ctx)
        player.shuffle_votes.add(ctx.author)

        if len(player.shuffle_votes) >= required:
            await ctx.send(":twisted_rightwards_arrows: Shuffling queue because vote to shuffle passed.")
            player.shuffle_votes.clear()
            random.shuffle(player.queue._queue)
        else:
            await ctx.send(
                f"Voted to shuffle the playlist. ({len(player.shuffle_votes)}/{required})",
            )

    @core.command()
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def announce(self, ctx: Context, toggle: bool):
        """
        Whether to announce the song.

        This will reset every time the bot joins a voice channel.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change whether the songs will be announced.")

        player.announce = toggle
        if toggle:
            return await ctx.send("Songs will be announced.")
        return await ctx.send("Song will no longer be announced.")

    @core.command()
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def duplicated(self, ctx: Context, toggle: bool):
        """
        Whether to allow duplicated in the queue.

        This will reset every time the bot joins a voice channel.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change whether duplicated songs are allowed.")

        player.allow_duplicates = toggle
        if toggle:
            return await ctx.send("Duplicate songs are now allowed.")
        return await ctx.send("Duplicate songs are no longer allowed in the queue.")

    @core.group(hybrid=True, name="filter", invoke_without_command=True)
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def filter_base(self, ctx: Context):
        await ctx.send_help(ctx.command)

    @filter_base.command(name="clear", aliases=["reset"])
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def filter_clear(self, ctx: Context):
        """
        Clears all filters from the player.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may clear filters.")

        await player.set_filter(wavelink.Filter(), seek=True)
        return await ctx.send("Cleared all filters.")

    @filter_base.command(name="equalizer", aliases=["eq"], invoke_without_command=True)
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(equalizer="The equalizer to set.")
    async def filter_equalizer(self, ctx: Context, *, equalizer: Literal["boost", "flat", "metal", "piano"]):
        """
        An equalizer for the player.

        There are four equalizers:
        Boost, Flat, Metal and Piano.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may set the equalizer.")

        eq_map = {
            "boost": wavelink.Equalizer.boost,
            "flat": wavelink.Equalizer.flat,
            "metal": wavelink.Equalizer.metal,
            "piano": wavelink.Equalizer.piano,
        }

        if equalizer.lower() not in eq_map:
            return await ctx.send("Please enter a valid equalizer.\nValid equalizers: boost, flat, metal, piano")

        await player.set_filter(wavelink.Filter(equalizer=eq_map[equalizer.lower()]()), seek=True)
        await ctx.send(f"Set the equalizer to {equalizer}.")

    @filter_base.command(name="karaoke")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(level="How much of an effect the filter should have.")
    async def filter_karaoke(self, ctx: Context, level: int = 1):
        """
        Karaoke filter tries to dampen the vocals and make the back track louder.

        This does not work well with all songs.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the karaoke filter.")

        await player.set_filter(wavelink.Filter(karaoke=wavelink.Karaoke(level=level, mono_level=level)), seek=True)
        await ctx.send(f"Set the karaoke filter to level {level}.")

    @filter_base.command(name="speed")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(speed="How fast the song will be played.")
    async def filter_speed(self, ctx: Context, speed: commands.Range[float, 0.25, 3.0]):
        """
        Sets the speed filter.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the speed.")

        await player.set_filter(wavelink.Filter(timescale=wavelink.Timescale(speed=speed)), seek=True)
        await ctx.send(f"Set the speed to {speed}x.")

    @filter_base.command(name="pitch")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(pitch="How high or low the song will be played.")
    async def filter_pitch(self, ctx: Context, pitch: commands.Range[float, 0.1, 5.0]):
        """
        Sets the pitch.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the pitch.")

        await player.set_filter(wavelink.Filter(timescale=wavelink.Timescale(pitch=pitch)), seek=True)
        await ctx.send(f"Set the pitch to {pitch}.")

    @filter_base.command(name="tremolo")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(frequency="How fast the volume should change.", depth="How much the volume should change.")
    async def filter_tremolo(
        self, ctx: Context, frequency: commands.Range[float, 1.0, 14.0], depth: commands.Range[float, 1.0, 100.0]
    ):
        """
        Creates a shuddering effect by quickly changing the volume.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the tremolo filter.")

        depth /= 100
        await player.set_filter(wavelink.Filter(tremolo=wavelink.Tremolo(frequency=frequency, depth=depth)), seek=True)
        await ctx.send(f"Set the tremolo filter to {frequency} frequency and {depth}% depth.")

    @filter_base.command(name="vibrato")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(frequency="How fast the pitch should change.", depth="How much the pitch should change.")
    async def filter_vibrato(
        self, ctx: Context, frequency: commands.Range[float, 1.0, 14.0], depth: commands.Range[float, 1.0, 100.0]
    ):
        """
        Creates a vibrating effect by quickly changing the pitch.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the vibrato filter.")

        depth /= 100
        await player.set_filter(wavelink.Filter(vibrato=wavelink.Vibrato(frequency=frequency, depth=depth)), seek=True)
        await ctx.send(f"Set the vibrato filter to {frequency:,} frequency and {depth*100}% depth.")

    @filter_base.command(name="rotation")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(speed="The speed the audio should rotate.")
    async def filter_rotation(self, ctx: Context, speed: float):
        """
        Creates a 3D effect by rotating the stereo channels.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the rotation filter.")

        await player.set_filter(wavelink.Filter(rotation=wavelink.Rotation(speed=speed)), seek=True)
        await ctx.send(f"Set the rotation filter speed to {speed}.")

    @filter_base.group(name="mix", invoke_without_command=True)
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def filter_mix(self, ctx: Context):
        """
        Allows you to control what channel audio from the track is actually played on.
        """
        await ctx.send_help(ctx.command)

    @filter_mix.command(name="only-left")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def filter_mix_only_left(self, ctx: Context):
        """
        Plays only the left channel
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the mix filter.")

        await player.set_filter(wavelink.Filter(channel_mix=wavelink.ChannelMix.only_left()), seek=True)
        await ctx.send("Set the mix filter to full left.")

    @filter_mix.command(name="only-right")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def filter_mix_only_right(self, ctx: Context):
        """
        Plays only the right channel.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the mix filter.")

        await player.set_filter(wavelink.Filter(channel_mix=wavelink.ChannelMix.only_right()), seek=True)
        await ctx.send("Set the mix filter to full right.")

    @filter_mix.command(name="mono")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def filter_mix_mono(self, ctx: Context):
        """
        Makes the audio channels mono.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the mix filter.")

        await player.set_filter(wavelink.Filter(channel_mix=wavelink.ChannelMix.mono()), seek=True)
        await ctx.send("Set the mix filter to mono.")

    @filter_mix.command(name="switch")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def filter_mix_switch(self, ctx: Context):
        """
        Switches the audio channels from left to right and right to left.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the mix filter.")

        await player.set_filter(wavelink.Filter(channel_mix=wavelink.ChannelMix.switch()), seek=True)
        await ctx.send("Set the mix filter switch.")

    @filter_base.command(name="lowpass")
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    @core.describe(smoothing="The factor by which the filter will block higher frequencies.")
    async def filter_lowpasss(self, ctx: Context, smoothing: float):
        """
        Suppresses higher frequencies while allowing lower frequencies to pass through.
        """
        player: Player = ctx.voice_client

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change change the lowpass filter.")

        await player.set_filter(wavelink.Filter(low_pass=wavelink.LowPass(smoothing=smoothing)), seek=True)
        await ctx.send(f"Set lowpass smoothing to {smoothing}")

    @core.command(hybrid=True, aliases=["q", "upnext"])
    @bot_in_voice()
    @in_bound_channel()
    async def queue(self, ctx: Context):
        """Display the players queued songs."""
        player: Player = ctx.voice_client

        if not player:
            return

        if player.queue.size == 0:
            return await ctx.send(f"The queue is empty. Use {ctx.prefix}play to add some songs!")

        entries = []
        for index, track in enumerate(player.queue._queue):
            entries.append(f"`{index + 1})` {track.hyperlink} [{track.requester.mention}]")

        pages = PaginatorSource(entries=entries, ctx=ctx)
        paginator = Paginator(source=pages, timeout=120, ctx=ctx, delete_message_after=True)
        await paginator.start()

    @core.command(aliases=["clq", "clqueue", "cqueue"])
    @in_voice()
    @bot_in_voice()
    @in_bound_channel()
    async def clearqueue(self, ctx: Context):
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
    @bot_in_voice()
    @in_bound_channel()
    async def nowplaying(self, ctx: Context):
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
    @bot_in_voice()
    @in_bound_channel()
    async def swap_dj(self, ctx: Context, *, member: discord.Member):
        """Swap the current DJ to another member in the voice channel."""
        player: Player = ctx.voice_client

        if not player:
            return

        if not self.is_privileged(ctx):
            return await ctx.send("Only admins and the DJ may use this command.")

        members = player.channel.members

        if member and member not in members:
            return await ctx.send(f"{member} is not currently in voice, so can not be a DJ.")

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
