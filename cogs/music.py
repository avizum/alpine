"""
Music cog ran my Obsidian.
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

import discord
import obsidian

from discord.ext import commands
from utils import AvimetryBot, AvimetryContext


class AvimetryPlayer(obsidian.PresetPlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def enqueue(self, track):
        super().enqueue(track)
        if not self.is_playing():
            await self.do_next()


class Music(commands.Cog):
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        if await self.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner('nope')

    @commands.command()
    async def join(self, ctx: AvimetryContext, *, channel: discord.VoiceChannel = None):
        if channel is None:
            if not ctx.author.voice:
                return await ctx.send('You are not in a channel.')
            channel = ctx.author.voice.channel

        player = ctx.bot.obsidian.get_player(ctx.guild, cls=AvimetryPlayer)
        try:
            await player.connect(channel)
        except discord.HTTPException:
            return await ctx.send('No permissions to join this channel.')
        else:
            await ctx.send(f'Joined {channel.mention}.')

    @commands.command()
    async def play(self, ctx: AvimetryContext, *, song: str):
        player = ctx.bot.obsidian.get_player(ctx.guild, cls=AvimetryPlayer)
        if not player.connected:
            join = ctx.bot.get_command('join')
            await join(ctx)

        if not player.connected:
            return

        track = await ctx.bot.obsidian.search_track(song, source=obsidian.Source.YOUTUBE)
        if not track:
            return await ctx.send('No songs were found.')

        await player.enqueue(track)
        if isinstance(track, obsidian.Track):
            await ctx.send(f'Added to queue: {track.title}')
        elif isinstance(track, obsidian.Playlist):
            await ctx.send(f'Added to queue: {track.name}')

    @commands.command(aliases=['disconnect'])
    async def leave(self, ctx: AvimetryContext):
        ctx.bot.obsidian.destroy_player(ctx.guild)
        await ctx.send('Left the channel.')

    @commands.command(aliases=['resume'])
    async def pause(self, ctx: AvimetryContext):
        player = ctx.bot.obsidian.get_player(ctx.guild, cls=AvimetryPlayer)
        if not player.connected:
            return
        new_pause = await player.set_pause()
        await ctx.send(f'Set pause to {new_pause}.')


def setup(bot: AvimetryBot):
    bot.add_cog(Music(bot))
