"""
Runs the bot.
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


class Music(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi


    @commands.command()
    async def join(self, ctx: AvimetryContext, *, channel: discord.VoiceChannel = None):
        if channel is None:
            if not ctx.author.voice:
                return await ctx.send('Please join a voice channel.')

            channel = ctx.author.voice.channel

        player = ctx.bot.obsidian.get_player(ctx.guild, cls=obsidian.PresetPlayer)
        try:
            await player.connect(channel)
        except discord.HTTPException:
            return await ctx.send('I may not have permissions to join VC.')
        else:
            await ctx.send('Connected')

    @commands.command()
    async def play(self, ctx: AvimetryContext, *, song: str):
        player = ctx.bot.obsidian.get_player(ctx.guild, cls=obsidian.PresetPlayer)
        if not player.connected:
            join = ctx.bot.get_command('join')
            await join(ctx)

        # Check a second time
        if not player.connected:
            return

        track = await ctx.bot.obsidian.search_track(song, source=obsidian.Source.YOUTUBE)
        if not track:
            return await ctx.send('No songs were found.')

        await player.play(track)
        await ctx.send(f'Now playing: {track.title}')

    @commands.command(aliases=['disconnect'])
    async def leave(self, ctx: AvimetryContext):
        ctx.bot.obsidian.destroy_player(ctx.guild)
        await ctx.send('Goodbye...')

    @commands.command(aliases=['resume'])
    async def pause(self, ctx: AvimetryContext):
        player = ctx.bot.obsidian.get_player(ctx.guild, cls=obsidian.PresetPlayer)
        if not player.connected:
            return

        new_pause = await player.set_pause()  # Let pause be handled automatically
        await ctx.send(f'Set pause to {new_pause}.')


def setup(avi: AvimetryBot):
    avi.add_cog(Music(avi))
