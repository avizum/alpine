"""
Owner only advanced debug cog.
Copyright (C) 2021 - present avizum

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
import jishaku
import discord
import sys
import psutil
import math

import toml
import utils
import core
import importlib

from discord.ext import commands, menus
from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES
from jishaku import Feature
from jishaku.codeblocks import codeblock_converter
from jishaku.flags import Flags
from jishaku.models import copy_context_with
from jishaku.paginators import PaginatorInterface
from utils import AvimetryBot, AvimetryContext, CogConverter, timestamp
from utils.paginators import AvimetryPages
from utils.converters import ModReason


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


class ErrorSource(menus.ListPageSource):
    def __init__(self, ctx: AvimetryContext, errors, *, per_page=1):
        super().__init__(entries=errors, per_page=per_page)
        self.ctx = ctx

    async def format_page(self, menu, page):
        embed = discord.Embed(title=f"Errors ({self.get_max_pages()} errors)")
        embed.add_field(
            name=f"{page['command']} | `{page['id']}`",
            value=f"```\n{page['error']}```",
            inline=False
        )
        embed.color = await self.ctx.determine_color()
        return embed


class GuildPageSource(menus.ListPageSource):
    def __init__(self, ctx: AvimetryContext, guilds: list[discord.Guild]):
        self.ctx = ctx
        super().__init__(guilds, per_page=2)

    async def format_page(self, menu, page):
        embed = discord.Embed(color=await self.ctx.determine_color())
        for guild in page:
            embed.add_field(
                name=guild.name,
                value=(
                    f"Owner: {guild.owner}\n"
                    f"Members: {guild.member_count}\n"
                    f"Created at: {discord.utils.format_dt(guild.created_at)}\n"
                    f"Joined at: {discord.utils.format_dt(guild.me.joined_at)}"
                ),
                inline=False
            )
        return embed


class Developer(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """
    Advanced debug cog for bot Developers.
    """
    def __init__(self, *args, **kwargs):
        self.emoji = "<:jishaku:913256121542791178>"
        super().__init__(*args, **kwargs)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        waste = "\U0001f5d1\U0000fe0f"
        if reaction.emoji == waste and await self.bot.is_owner(user) and reaction.message.author == self.bot.user:
            await reaction.message.delete()

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
        """
        Run a command, bypassing all checks.
        """
        alt_ctx = await copy_context_with(ctx, content=f"{ctx.prefix}{command_string}")
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.reinvoke(alt_ctx)

    @Feature.Command(parent="jsk", name="in", aliases=["channel", "inside"])
    async def jsk_in(self, ctx: AvimetryContext, channel: discord.TextChannel, *, command_string):
        """
        Run a command in another channel.
        """
        alt_ctx = await copy_context_with(ctx, channel=channel)
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.invoke(alt_ctx)

    @Feature.Command(parent="jsk", name="tasks")
    async def jsk_tasks(self, ctx: AvimetryContext):
        """
        Shows the currently running jishaku tasks.
        """

        if not self.tasks:
            return await ctx.send("No currently running tasks.")

        paginator = commands.Paginator(max_size=1985, prefix="", suffix="")

        for task in self.tasks:
            paginator.add_line(f"{task.index}: `{task.ctx.command.qualified_name}`, invoked at "
                               f"{discord.utils.format_dt(task.ctx.message.created_at)} "
                               f"({discord.utils.format_dt(task.ctx.message.created_at, 'R')})")

        interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        return await interface.send_to(ctx)

    @Feature.Command(name="jishaku", aliases=["jsk"], hidden=Flags.HIDE,
                     invoke_without_command=True, ignore_extra=True, extras={'user_permissions': ['bot_owner']})
    async def jsk(self, ctx: AvimetryContext):
        """
        The Jishaku debug and diagnostic commands.

        This command on its own gives a status brief.
        All other functionality is within its subcommands.
        """
        summary = [
            f"Jishaku `v{jishaku.__version__}`, discord.py (official spork) `v{discord.__version__}`, "
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
            summary.append(f"{presence_intent} and {members_intent}.")
        else:
            guild_subs = self.bot._connection.guild_subscriptions
            guild_subscriptions = f"`guild subscriptions` are `{'enabled' if guild_subs else 'disabled'}`"
            summary.append(f"{message_cache} and {guild_subscriptions}.")
        summary.append("")

        summary.append(f"Average websocket latency: `{round(self.bot.latency * 1000)}ms`")

        jishaku_embed = discord.Embed(description="\n".join(summary))
        await ctx.send(embed=jishaku_embed)

    @core.group(
        invoke_without_command=True,
        aliases=["dev"],
        user_permissions='Bot Owner',
    )
    async def developer(self, ctx: AvimetryContext):
        """
        Commands for bot devlopers.
        """
        jishaku = self.bot.get_command('jishaku')
        await jishaku(ctx)

    @developer.command()
    async def news(self, ctx: AvimetryContext, *, news: str):
        with open("config.toml", "r") as afile:
            load = toml.loads(afile.read())
            load["news"]["news"] = news
        with open("config.toml", "w") as bfile:
            toml.dump(load, bfile)
            self.bot.news = news
        embed = discord.Embed(title="Successfully Set News.", description=f"Here is the preview.\n{news}")
        await ctx.send(embed=embed)

    @developer.command()
    async def ilreload(self, ctx: AvimetryContext, module: str):
        try:
            m = importlib.reload(__import__(module))
            await ctx.send(f"Reloaded Sucessfully: `{m}`")
        except Exception as exc:
            await ctx.send(exc)

    @developer.command(aliases=["l"])
    async def load(self, ctx: AvimetryContext, *module: str):
        """
        Load cogs.
        """
        if module[0] in ["~", "*", "a", "all"]:
            await ctx.send("Loaded all extensions.")
            return await self.bot.load_extensions()
        load_list = []
        for cog in module:
            try:
                self.bot.load_extension(cog)
                load_list.append(f'{self.bot.emoji_dictionary["green_tick"]} | {cog}')
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                load_list.append(f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        embed = discord.Embed(title="Loaded cogs", description="\n".join(load_list))
        await ctx.send(embed=embed)

    @developer.command(aliases=["u"])
    async def unload(self, ctx: AvimetryContext, module: CogConverter):
        """
        Unload cogs.
        """
        unload_list = []
        for cog in module:
            try:
                self.bot.unload_extension(cog)
                unload_list.append(f'{self.bot.emoji_dictionary["green_tick"]} | {cog}')
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                unload_list.append(f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        embed = discord.Embed(title="Unloaded cogs", description="\n".join(unload_list))
        await ctx.send(embed=embed)

    @developer.command(aliases=["r"])
    async def reload(self, ctx: AvimetryContext, module: CogConverter):
        """
        Reload cogs
        """
        reload_list = []
        for cog in module:
            try:
                self.bot.reload_extension(cog)
                reload_list.append(f'{self.bot.emoji_dictionary["green_tick"]} | {cog}')
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                reload_list.append(f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        description = "\n".join(reload_list)
        embed = discord.Embed(title="Reloaded cogs", description=description)
        await ctx.send(embed=embed)

    @developer.command()
    async def sync(self, ctx: AvimetryContext):
        """
        Pulls from GitHub then reloads all modules.

        If the command fails to unload, It will show the module and error.
        """
        sync_embed = discord.Embed(
            title="Syncing with GitHub", description="Please Wait..."
        )
        edit_sync = await ctx.send(embed=sync_embed)
        proc = await asyncio.create_subprocess_shell(
            'git pull',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await proc.communicate()

        if stdout:
            output = f'[stdout]\n{stdout.decode()}'
        elif stderr:
            output = f'[stderr]\n{stderr.decode()}'

        sync_embed.description = f"```bash\n{output}\n```"
        sync_embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        sync_embed.title = "Synced With GitHub"
        modules = await CogConverter().convert(ctx, "~")
        reload_list = []
        for cog in modules:
            try:
                self.bot.reload_extension(cog)
            except commands.ExtensionError as e:
                reload_list.append(f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        if not reload_list:
            value = "All modules were reloaded successfully"
        else:
            value = "\n".join(reload_list)
        sync_embed.add_field(name="Reloaded Modules", value=value)
        await edit_sync.edit(embed=sync_embed)

    @developer.command(aliases=["shutdown"])
    async def reboot(self, ctx: AvimetryContext):
        """
        Reboot or shutdown the bot.
        """
        sm = discord.Embed(
            description=f"Are you sure you want to {ctx.invoked_with}?"
        )
        conf = await ctx.confirm(embed=sm)
        if conf.result:
            await self.bot.close()
        if not conf:
            await conf.message.edit(content=f"{ctx.invoked_with.capitalize()} Aborted", embed=None, delete_after=5)

    @developer.command()
    async def eval(self, ctx: AvimetryContext, *, code: codeblock_converter):
        """
        Direct evaluation of python code.

        This command is an alias of `jishaku py`.
        """
        jsk = self.bot.get_command("jsk py")
        if jsk:
            await jsk(ctx, argument=code)
        else:
            await ctx.send("Jishaku is not loaded.")

    @developer.command(brief="Leaves a server.")
    async def leave(self, ctx: AvimetryContext, guild: discord.Guild):
        """
        Command to leave a guild that may be abusing the bot.
        """
        conf = await ctx.confirm(f"Are you sure you want me to leave {guild.name} ({guild.id})?")
        if conf.result:
            await ctx.guild.leave()
            return await ctx.message.add_reaction(self.bot.emoji_dictionary["green_tick"])
        await conf.message.edit(content="Okay, Aborted.")

    @developer.group(
        invoke_without_command=True,
        aliases=["bl"]
    )
    async def blacklist(self, ctx: AvimetryContext):
        """
        Show the User IDs for the currently blacklisted people.
        """
        bl_users = ctx.cache.blacklist.keys()
        joiner = "\n"
        embed = discord.Embed(
            title=f"List of blacklisted users ({len(bl_users)})",
            description=f"```\n{joiner.join([str(bl) for bl in bl_users])}```"
        )
        await ctx.send(embed=embed)

    @blacklist.command(name="add", aliases=["a"])
    async def blacklist_add(self, ctx: AvimetryContext, user: discord.User, *, reason: ModReason = None):
        """
        Adds a user to the global blacklist.
        """
        reason = reason or f"{ctx.author}: No reason provided, Ask in support server."
        if user.id in self.bot.owner_ids:
            return await ctx.send("Nope, won't do that.")
        try:
            ctx.cache.blacklist[user.id]
            return await ctx.send(f"{user} is already blacklisted.")
        except KeyError:
            query = "INSERT INTO blacklist VALUES ($1, $2)"
            await self.bot.pool.execute(query, user.id, reason)
            ctx.cache.blacklist[user.id] = reason

        embed = discord.Embed(
            title="Blacklisted User",
            description=(
                f"Added {user} to the blacklist.\n"
                f"Reason: `{reason}`"
            )
        )
        await ctx.send(embed=embed)

    @blacklist.command(
        name="remove",
        aliases=["r"]
    )
    async def blacklist_remove(self, ctx: AvimetryContext, user: discord.User, *, reason=None):
        """
        Removes a user from the global blacklist.
        """
        try:
            ctx.cache.blacklist[user.id]
        except KeyError:
            return await ctx.send(f"{user} is not blacklisted")
        query = "DELETE FROM blacklist WHERE user_id=$1"
        await self.bot.pool.execute(query, user.id)
        self.bot.cache.blacklist.pop(user.id)
        await ctx.send(f"Unblacklisted {user}. Reason: {reason}")

    @developer.command()
    async def cleanup(self, ctx: AvimetryContext, amount: int = 15):
        """
        Delete only the bot messages.

        Goes through channel history and then deletes them one by one.
        """
        def check(m: discord.Message):
            return m.author == self.bot.user
        perms = ctx.channel.permissions_for(ctx.me).manage_messages
        purged = await ctx.channel.purge(limit=amount, check=check, bulk=perms)
        cog = self.bot.get_cog("moderation")
        await ctx.can_delete(embed=await cog.do_affected(purged))

    @developer.command()
    async def maintenance(self, ctx: AvimetryContext, toggle: bool):
        """
        Enables maintenance mode.

        When maintenance mode is enabled, The bot will only locked to devlopers.
        """
        match = {
            True: "enabled",
            False: "disabled"
        }
        self.bot.maintenance = toggle
        await ctx.send(f"Maintenance mode has been {match[toggle]}")

    @developer.command()
    async def cogs(self, ctx: AvimetryContext, cog: str = None):
        """
        Shows all the loaded cogs and how long ago they were loaded.
        """
        thing_list = [
            f"{key.title()} | Loaded {utils.timestamp(val.load_time, 'R')}"
            for key, val in self.bot.cogs.items()
        ]
        embed = discord.Embed(title="Loaded Cogs", description='\n'.join(thing_list))
        await ctx.send(embed=embed)

    @developer.command()
    async def guilds(self, ctx: AvimetryContext):
        source = GuildPageSource(ctx, guilds=self.bot.guilds)
        pages = AvimetryPages(source, ctx=ctx, disable_view_after=True)
        await pages.start()

    @developer.group(invoke_without_command=True, aliases=["error"])
    async def errors(self, ctx: AvimetryContext):
        """
        Show all the errors in the bot.
        """
        errors = await self.bot.pool.fetch('SELECT * FROM command_errors WHERE fixed = false')
        if not errors:
            embed = discord.Embed(title="Errors", description="No active errors have been found.")
            return await ctx.send(embed=embed)
        else:
            menu = AvimetryPages(ErrorSource(ctx, errors), ctx=ctx, delete_message_after=True)
            return await menu.start()

    @errors.command()
    async def fixed(self, ctx: AvimetryContext):
        """
        Shows all fixed errors.
        """
        errors = await self.bot.pool.fetch('SELECT * FROM command_errors WHERE fixed = True')
        if not errors:
            embed = discord.Embed(title="Errors", description="No fixed errors have been found.")
            return await ctx.send(embed=embed)
        else:
            menu = AvimetryPages(ErrorSource(ctx, errors, per_page=2), ctx=ctx, delete_message_after=True)
            return await menu.start()

    @errors.command()
    async def fix(self, ctx: AvimetryContext, *error_id: int):
        """
        Marks an error as fixed.

        Giving multiple IDs will mark all of them as fixed.
        """
        fix_list = []
        for i in error_id:
            query = "SELECT * FROM command_errors WHERE id=$1"
            error_info = await self.bot.pool.fetchrow(query, i)
            if not error_info:
                fix_list.append(f"Error ID {i} does not exist.")
            elif error_info['fixed'] is True:
                fix_list.append(f"Error ID {i} is already marked as fixed.")
            else:
                query = "UPDATE command_errors SET fixed=$1 WHERE id=$2"
                await self.bot.pool.execute(query, True, i)
                fix_list.append(f"Error ID {i} has been marked as fixed.")
        await ctx.send('\n'.join(fix_list))

    @developer.command(aliases=["dmsg", "dmessage", "delmsg", "deletem", "deletemsg", "delmessage"])
    async def deletemessage(self, ctx: AvimetryContext, message: discord.Message = None):
        if message is None and ctx.reference is not None:
            if ctx.reference.author == ctx.me:
                await ctx.reference.delete()
            else:
                return await ctx.message.add_reaction(self.bot.emoji_dictionary["red_tick"])
        if message and message.author == ctx.me:
            await message.delete()
        return await ctx.message.add_reaction(self.bot.emoji_dictionary["green_tick"])


def setup(bot: AvimetryBot):
    bot.add_cog(Developer(bot=bot))
