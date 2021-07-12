"""
Owner only advanced debug cog.
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

import jishaku
import discord
import sys
import platform
import psutil
import math

from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from jishaku import Feature
from jishaku.flags import JISHAKU_HIDE
from utils import AvimetryBot, AvimetryContext, CogConverter, timestamp


def naturalsize(size_in_bytes: int):
    """
    Converts a number of bytes to an appropriately-scaled unit
    E.g.:
        1024 -> 1.00 KiB
        12345678 -> 11.77 MiB
    """
    units = ('B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB')

    power = int(math.log(size_in_bytes, 1024))

    return f"{size_in_bytes / (1024 ** power):.2f} {units[power]}"


class Jishaku(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """
    Advanced debug cog.
    """
    @Feature.Command(parent="jsk", name="load", aliases=["l"])
    async def jsk_load(self, ctx: AvimetryContext, module: CogConverter):
        command = self.bot.get_command("dev load")
        await command(ctx, module=module)

    @Feature.Command(parent="jsk", name="unload", aliases=["u"])
    async def jsk_unload(self, ctx: AvimetryContext, module: CogConverter):
        command = self.bot.get_command("dev unload")
        await command(ctx, module=module)

    @Feature.Command(parent="jsk", name="reload", aliases=["r"])
    async def jsk_reload(self, ctx: AvimetryContext, module: CogConverter):
        command = self.bot.get_command("dev reload")
        await command(ctx, module=module)

    @Feature.Command(parent="jsk", name="sync", aliases=["pull"])
    async def jsk_sync(self, ctx: AvimetryContext):
        command = self.bot.get_command("dev sync")
        await command(ctx)

    @Feature.Command(name="jishaku", aliases=["jsk", "jks", "bishaku", "bsk", "bks"], hidden=JISHAKU_HIDE,
                     invoke_without_command=True, ignore_extra=False)
    async def jsk(self, ctx: AvimetryContext):
        summary = [
            f"Jishaku `v{jishaku.__version__}`, discord.py `v{discord.__version__}`, "
            f"Python `{platform.python_version()}` on `{sys.platform}`, ",
            f"Jishaku was loaded {timestamp(self.load_time, 'R')} "
            f"and the cog was loaded {timestamp(self.start_time, 'R')}.",
            ""
        ]
        try:
            proc = psutil.Process()
            with proc.oneshot():
                try:
                    mem = proc.memory_full_info()
                    summary.append(
                        f"I am using {naturalsize(mem.rss)} physical memory and "
                        f"{naturalsize(mem.vms)} virtual memory, "
                        f"{naturalsize(mem.uss)} of which is unique to this process."
                    )
                except psutil.AccessDenied:
                    pass

                try:
                    name = proc.name()
                    pid = proc.pid
                    thread_count = proc.num_threads()
                    summary.append(
                        f"I am running on Process ID `{pid}` (`{name}`) with {thread_count} threads.")
                except psutil.AccessDenied:
                    pass
                summary.append("")

        except psutil.AccessDenied:
            summary.append("psutil is installed but this process does not have access to display this information")
            summary.append("")

        guilds = len(self.bot.guilds)
        members = len([m for m in self.bot.users if not m.bot])
        bots = len([m for m in self.bot.users if m.bot])
        total = len(self.bot.users)

        cache_summary = f"I can see {guilds} guilds, {members} humans, and {bots} bots, totaling to {total} users."

        if isinstance(self.bot, discord.AutoShardedClient):
            summary.append(
                f"I am automatically sharded ({len(self.bot.shards)} shards of {self.bot.shard_count})"
                f" and can see {cache_summary}"
            )
        elif self.bot.shard_count:
            summary.append(f"I am manually sharded and {cache_summary}")
        else:
            summary.append(f"I am not sharded and {cache_summary}")

        if self.bot._connection.max_messages:
            message_cache = f"Message cache is capped at {self.bot._connection.max_messages}."
        else:
            message_cache = "Message cache is not enabled."
        summary.append(message_cache)

        if discord.version_info >= (1, 5, 0):
            presence_intent = f"presences `{'enabled' if self.bot.intents.presences else 'disabled'}`"
            members_intent = f"members `{'enabled' if self.bot.intents.members else 'disabled'}`"
            summary.append(f"Intents: {presence_intent} and {members_intent}.")
        else:
            guild_subs = self.bot._connection.guild_subscriptions
            guild_subscriptions = f"`guild subscriptions` are `{'enabled' if guild_subs else 'disabled'}`"
            summary.append(f"{message_cache} and {guild_subscriptions}.")
        summary.append("")

        summary.append(f"Average websocket latency: `{round(self.bot.latency * 1000)}ms`")

        jishaku_embed = discord.Embed(description="\n".join(summary))
        await ctx.send(embed=jishaku_embed)


def setup(avi: AvimetryBot):
    avi.add_cog(Jishaku(bot=avi))
