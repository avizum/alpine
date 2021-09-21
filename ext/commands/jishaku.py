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
import psutil
import math

from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from jishaku import Feature
from jishaku.models import copy_context_with
from jishaku.flags import Flags
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
    @Feature.Command(parent="jsk", name="shutdown", aliases=["fuckoff", "logout", "die", "reboot", "rb"])
    async def jsk_shutdown(self, ctx: AvimetryContext):
        """
        Reboot or shutdown the bot.
        """
        command = self.bot.get_command('dev reboot')
        await command(ctx)

    @Feature.Command(parent="jsk", name="load", aliases=["l"])
    async def jsk_load(self, ctx: AvimetryContext, module: CogConverter):
        """
        Load cogs.
        """
        command = self.bot.get_command("dev load")
        await command(ctx, module)

    @Feature.Command(parent="jsk", name="unload", aliases=["u"])
    async def jsk_unload(self, ctx: AvimetryContext, module: CogConverter):
        """
        Unload cogs.
        """
        command = self.bot.get_command("dev unload")
        await command(ctx, module)

    @Feature.Command(parent="jsk", name="reload", aliases=["r"])
    async def jsk_reload(self, ctx: AvimetryContext, module: CogConverter):
        """
        Reload cogs
        """
        command = self.bot.get_command("dev reload")
        await command(ctx, module)

    @Feature.Command(parent="jsk", name="sync", aliases=["pull"])
    async def jsk_sync(self, ctx: AvimetryContext):
        """
        Pulls from GitHub then reloads all modules.

        If the command fails to unload, It will show the module and error.
        """
        command = self.bot.get_command("dev sync")
        await command(ctx)

    @Feature.Command(parent="jsk", name="battery")
    async def jsk_battery(self, ctx: AvimetryContext):
        """
        Shows the system battery.
        """
        battery = psutil.sensors_battery()
        plugged = battery.power_plugged
        percent = str(battery.percent)
        await ctx.send(f"System battery is at {percent}% and {'Plugged in' if plugged else 'Unplugged'}")

    @Feature.Command(parent="jsk", name="su")
    async def jsk_su(self, ctx: AvimetryContext, member: discord.Member, *, command_string):
        """
        Run a command as someone else.
        """
        alt_ctx = await copy_context_with(ctx, author=member, content=f"{ctx.prefix}{command_string}")
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.invoke(alt_ctx)

    @Feature.Command(parent="jsk", name="sudo", aliases=["admin", "bypass"])
    async def jsk_sudo(self, ctx: AvimetryContext, *, command_string):
        alt_ctx = await copy_context_with(ctx, content=f"{ctx.prefix}{command_string}")
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.reinvoke(alt_ctx)

    @Feature.Command(parent="jsk", name="in", aliases=["channel", "inside"])
    async def jsk_in(self, ctx: AvimetryContext, channel: discord.TextChannel, *, command_string):
        alt_ctx = await copy_context_with(ctx, channel=channel)
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.invoke(alt_ctx)

    @Feature.Command(name="jishaku", aliases=["jsk"], hidden=Flags.HIDE,
                     invoke_without_command=True, ignore_extra=True, extras={'user_permissions': ['bot_owner']})
    async def jsk(self, ctx: AvimetryContext):
        """
        The Jishaku debug and diagnostic commands.

        This command on its own gives a status brief.
        All other functionality is within its subcommands.
        """
        summary = [
            f"Jishaku `v{jishaku.__version__}`, discord.py (official fork) `v{discord.__version__}`, "
            f"Python `{sys.version}` on `{sys.platform}`, ".replace("\n", ""),
            f"Jishaku was loaded {timestamp(self.load_time, 'R')} "
            f"and module was loaded {timestamp(self.start_time, 'R')}.",
            ""
        ]
        try:
            proc = psutil.Process()
            with proc.oneshot():
                try:
                    mem = proc.memory_full_info()
                    summary.append(
                        f"This process is using {naturalsize(mem.rss)} physical memory and "
                        f"{naturalsize(mem.vms)} virtual memory, "
                        f"{naturalsize(mem.uss)} of which is unique to this process."
                    )
                except psutil.AccessDenied:
                    pass

                try:
                    name = proc.name()
                    pid = proc.pid
                    tc = proc.num_threads()
                    summary.append(
                        f"This process is running on Process ID `{pid}` (`{name}`) with {tc} threads.")
                except psutil.AccessDenied:
                    pass
                summary.append("")

        except psutil.AccessDenied:
            summary.append("psutil is installed but this process does not have access to display this information")
            summary.append("")

        guilds = f"{len(self.bot.guilds)} guilds"
        humans = f"{sum(not m.bot for m in self.bot.users)} humans"
        bots = f"{sum(m.bot for m in self.bot.users)} bots"
        users = f"{len(self.bot.users)} users"

        cache_summary = f"can see {guilds}, {humans}, and {bots}, totaling to {users}."

        if isinstance(self.bot, discord.AutoShardedClient):
            if len(self.bot.shards) > 20:
                summary.append(
                    f"This bot is automatically sharded ({len(self.bot.shards)} shards of {self.bot.shard_count})"
                    f" and can see {cache_summary}"
                )
            else:
                shard_ids = ', '.join(str(i) for i in self.bot.shards.keys())
                summary.append(
                    f"This bot is automatically sharded (Shards {shard_ids} of {self.bot.shard_count})"
                    f" and can see {cache_summary}"
                )
        elif self.bot.shard_count:
            summary.append(
                f"This bot is manually sharded (Shard {self.bot.shard_id} of {self.bot.shard_count})"
                f" and can see {cache_summary}"
            )
        else:
            summary.append(f"This bot is not sharded and {cache_summary}")

        if self.bot._connection.max_messages:
            message_cache = f"Message cache is capped at {self.bot._connection.max_messages}."
        else:
            message_cache = "Message cache is not enabled."
        summary.append(message_cache)

        if discord.version_info >= (1, 5, 0):
            presence_intent = f"Presences intent `{'enabled' if self.bot.intents.presences else 'disabled'}`"
            members_intent = f"Members intent `{'enabled' if self.bot.intents.members else 'disabled'}`"
            summary.append(f" {presence_intent} and {members_intent}.")
        else:
            guild_subs = self.bot._connection.guild_subscriptions
            guild_subscriptions = f"`guild subscriptions` are `{'enabled' if guild_subs else 'disabled'}`"
            summary.append(f"{message_cache} and {guild_subscriptions}.")
        summary.append("")

        summary.append(f"Average websocket latency: `{round(self.bot.latency * 1000)}ms`")

        jishaku_embed = discord.Embed(description="\n".join(summary))
        await ctx.send(embed=jishaku_embed)


def setup(bot: AvimetryBot):
    bot.add_cog(Jishaku(bot=bot))
