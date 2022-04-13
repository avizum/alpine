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

from __future__ import annotations

import asyncio
import datetime
import importlib
import inspect
import math
import re
import sys
from typing import List
from difflib import get_close_matches

import discord
import psutil
import toml
import utils
from asyncpg import Record
from discord.ext import commands, menus
from jishaku import Feature
from jishaku.cog import OPTIONAL_FEATURES, STANDARD_FEATURES
from jishaku.codeblocks import codeblock_converter
from jishaku.flags import Flags
from jishaku.models import copy_context_with
from jishaku.modules import package_version
from jishaku.paginators import PaginatorInterface
from jishaku.repl import AsyncCodeExecutor, get_var_dict_from_ctx
from jishaku.exception_handling import ReplResponseReactor
from jishaku.functools import AsyncSender
from jishaku.paginators import WrappedPaginator
from importlib.metadata import distribution, packages_distributions

import core
from core import Bot, Context
from utils.helpers import timestamp
from utils.converters import ModReason
from utils.paginators import Paginator, PaginatorEmbed
from utils.view import View


def naturalsize(size_in_bytes: int) -> str:
    """
    Converts a number of bytes to an appropriately-scaled unit
    E.g.:
        1024 -> 1.00 KiB
        12345678 -> 11.77 MiB
    """
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")

    power = int(math.log(size_in_bytes, 1024))

    return f"{size_in_bytes / (1024 ** power):.2f} {units[power]}"

class CogConverter(commands.Converter):
    async def convert(self, ctx: Context, argument):
        exts = []
        if argument in ["~", "*", "a", "all"]:
            exts.extend(ctx.bot.extensions)
        elif argument not in ctx.bot.extensions:
            arg = get_close_matches(argument, ctx.bot.extensions)
            if arg:
                exts.append(arg[0])
        else:
            exts.append(argument)
        return exts

class ErrorSource(menus.ListPageSource):
    def __init__(self, ctx: Context, errors: List[Record], *, title: str = "Errors", per_page: int = 1) -> None:
        super().__init__(entries=errors, per_page=per_page)
        self.ctx = ctx
        self.title = title

    async def format_page(self, menu: menus.Menu, page: List[Record]) -> discord.Embed:
        embed = discord.Embed(title=self.title, color=await self.ctx.fetch_color())
        for error in page:
            embed.add_field(
                name=f"{error['command']} | `{error['id']}`",
                value=f"```\n{error['error']}```",
                inline=False,
            )
        return embed

class GuildPageSource(menus.ListPageSource):
    def __init__(self, ctx: Context, guilds: List[discord.Guild]) -> None:
        self.ctx = ctx
        super().__init__(guilds, per_page=2)

    async def format_page(self, menu: menus.Menu, page: List[discord.Guild]) -> discord.Embed:
        embed = PaginatorEmbed(ctx=self.ctx)
        for guild in page:
            embed.add_field(
                name=guild.name,
                value=(
                    f"Owner: {guild.owner}\n"
                    f"Members: {guild.member_count}\n"
                    f"Created at: {discord.utils.format_dt(guild.created_at)}\n"
                    f"Joined at: {discord.utils.format_dt(guild.me.joined_at)}"
                ),
                inline=False,
            )
        return embed

class BlacklistedPageSource(menus.ListPageSource):
    def __init__(self, ctx: Context, blacklisted: List[int]) -> None:
        self.ctx = ctx
        super().__init__(blacklisted, per_page=2)

    async def format_page(self, menu: menus.Menu, page: List[int]) -> discord.Embed:
        embed = PaginatorEmbed(ctx=self.ctx, title="Blacklisted Users")
        for entry in page:
            user = self.ctx.bot.get_user(entry)
            bl_entry = self.ctx.cache.blacklist[entry]
            embed.add_field(name=f"{user}({user.id})" if user else entry, value=f"[Reason]\n{bl_entry}", inline=False)
        return embed

class ReloadView(View):
    def __init__(self, ctx: Context, bot: Bot, to_reload: list[str], embed: discord.Embed) -> None:
        self.ctx = ctx
        self.bot = bot
        self.embed = embed
        self.to_reload = None
        self.get_close_cogs(to_reload)
        super().__init__(member=self.ctx.author, timeout=60)

    def get_close_cogs(self, argument: list[str]) -> list[str]:
        self.to_reload = [get_close_matches(cog, self.bot.extensions)[0] for cog in argument]

    @discord.ui.button(label="Reload", style=discord.ButtonStyle.blurple)
    async def reload_modules(self, interaction: discord.Interaction, button: discord.Button):
        reload_list = []
        for cog in self.to_reload:
            try:
                await self.bot.reload_extension(cog)
                reload_list.append(f"{self.bot.emoji_dictionary['green_tick']} | {cog}")
            except commands.ExtensionError as e:
                reload_list.append(f"{self.bot.emoji_dictionary['red_tick']} | {cog}\n```{e}```")
            else:
                if not reload_list:
                    self.embed.add_field(name="Reloaded Modules", value="No modules were reloaded")
                else:
                    self.embed.add_field(name="Reloaded Modules", value="\n".join(reload_list))
        self.embed.set_footer()
        await interaction.response.edit_message(embed=self.embed, view=None)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel_reload(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.edit_message(view=None)
        self.stop()

FILE_REGEX = re.compile(r"^(.*[^/\n]+)(\.py)")

class Owner(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """
    Advanced debug cog for bot Developers.
    """

    def __init__(self, bot: Bot, **kwargs) -> None:
        self.emoji = "<:jishaku:913256121542791178>"
        self.bot = bot
        super().__init__(bot=bot, **kwargs)
        for i in self.walk_commands():
            i.member_permissions = ["Bot Owner"]

    @core.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member) -> None:
        waste = "\U0001f5d1\U0000fe0f"
        if (
            reaction.emoji == waste
            and await self.bot.is_owner(user)
            and reaction.message.author == self.bot.user
        ):
            await reaction.message.delete()

    @Feature.Command(
        name="jishaku",
        aliases=["jsk", "dev", "developer"],
        hidden=Flags.HIDE,
        invoke_without_command=True,
        ignore_extra=False,
        extras={"member_permissions": ["bot_owner"]},
    )
    async def jsk(self, ctx: Context):
        """
        The Jishaku debug and diagnostic commands.

        This command on its own gives a status brief.
        All other functionality is within its subcommands.
        """
        distributions = [
            dist for dist in packages_distributions()["discord"]
            if any(
                file.parts == ("discord", "__init__.py")
                for file in distribution(dist).files
            )
        ]

        if distributions:
            dist_version = f"{distributions[0]} `{package_version(distributions[0])}`"
        else:
            dist_version = f"unknown `{discord.__version__}`"

        summary = [
            f"Jishaku `v{package_version('jishaku')}`, {dist_version}, "
            f"Python `{sys.version}` on `{sys.platform}`, ".replace("\n", ""),
            f"Jishaku was loaded {timestamp(self.load_time, 'R')} "
            f"and cog was loaded {timestamp(self.start_time, 'R')}.",
            "",
        ]
        if psutil:
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

                        summary.append(f"This process is running on  PID `{pid}` (`{name}`) with {tc} threads.")
                    except psutil.AccessDenied:
                        pass
                    summary.append("")

            except psutil.AccessDenied:
                summary.append("psutil is installed but this process does not have access to display this information")
                summary.append("")

        guilds = f"{len(self.bot.guilds):,} guilds"
        humans = f"{sum(not m.bot for m in self.bot.users):,} humans"
        bots = f"{sum(m.bot for m in self.bot.users):,} bots"
        users = f"{len(self.bot.users):,} users"

        cache_summary = f"can see {guilds}, {humans}, and {bots}, totaling to {users}."

        if isinstance(self.bot, discord.AutoShardedClient):
            if len(self.bot.shards) > 20:
                summary.append(
                    f"This bot is automatically sharded ({len(self.bot.shards)} shards of {self.bot.shard_count}) "
                    f"and {cache_summary}"
                )
            else:
                shard_ids = ", ".join(str(i) for i in self.bot.shards.keys())
                summary.append(
                    f"This bot is automatically sharded (Shards {shard_ids} of {self.bot.shard_count})"
                    f"and {cache_summary}"
                )
        elif self.bot.shard_count:
            summary.append(
                f"This bot is manually sharded (Shard {self.bot.shard_id} of {self.bot.shard_count})"
                f"and {cache_summary}"
            )
        else:
            summary.append(f"This bot is not sharded and {cache_summary}")

        if self.bot._connection.max_messages:
            message_cache = (
                f"Message cache is capped at {self.bot._connection.max_messages}."
            )
        else:
            message_cache = "Message cache is not enabled."
        summary.append(message_cache)

        presence_intent = f"Presences intent `{'enabled' if self.bot.intents.presences else 'disabled'}`"
        members_intent = f"Members intent `{'enabled' if self.bot.intents.members else 'disabled'}`"
        message_intent = f"Message intent `{'enabled' if self.bot.intents.message_content else 'disabled'}`"
        summary.append(f"{presence_intent}, {members_intent} and {message_intent}.")
        summary.append("")

        summary.append(f"Average websocket latency: `{round(self.bot.latency * 1000)}ms`")

        jishaku_embed = discord.Embed(description="\n".join(summary))
        await ctx.send(embed=jishaku_embed)

    @Feature.Command(parent="jsk", name="py", aliases=["python"])
    async def jsk_python(self, ctx: Context, *, argument: codeblock_converter):
        """
        Direct evaluation of Python code.
        """

        arg_dict = get_var_dict_from_ctx(ctx, Flags.SCOPE_PREFIX)
        message_reference = getattr(ctx.message.reference, "resolved", None)
        arg_dict["reference"] = message_reference
        arg_dict["ref"] = message_reference
        arg_dict["core"] = core
        arg_dict["source"] = inspect.getsource
        arg_dict["_"] = self.last_result

        scope = self.scope

        try:
            async with ReplResponseReactor(ctx.message):
                with self.submit(ctx):
                    executor = AsyncCodeExecutor(argument.content, scope, arg_dict=arg_dict)
                    async for send, result in AsyncSender(executor):
                        if result is None:
                            continue

                        self.last_result = result

                        send(await self.jsk_python_result_handling(ctx, result))

        finally:
            scope.clear_intersection(arg_dict)

    @Feature.Command(parent="jsk", name="shutdown", aliases=["reboot", "logout", "rb", "rs"])
    async def jsk_shutdown(self, ctx: Context):
        """
        Reboot the bot.
        """
        sm = discord.Embed(description="Are you sure you want to reboot?")
        conf = await ctx.confirm(embed=sm)
        if conf.result:
            with open("reboot.toml", "w") as f:
                toml.dump(
                    {
                        "message_id": conf.message.id,
                        "channel_id": ctx.channel.id,
                        "restart_time": datetime.datetime.now(tz=datetime.timezone.utc),
                    },
                    f,
                )
            await conf.message.edit(content="Rebooting...", embed=None)
            await self.bot.close()
        if not conf:
            await conf.message.edit(
                content="Reboot aborted", embed=None, delete_after=5
            )

    @Feature.Command(parent="jsk", name="battery")
    async def jsk_battery(self, ctx: Context):
        """
        Shows the system battery.
        """
        battery = psutil.sensors_battery()
        plugged = battery.power_plugged
        percent = str(battery.percent)
        await ctx.send(
            f"System battery is at {percent}% and {'Plugged in' if plugged else 'Unplugged'}"
        )

    @Feature.Command(parent="jsk", name="su")
    async def jsk_su(self, ctx: Context, member: discord.Member, *, command_string):
        """
        Run a command as someone else.
        """
        alt_ctx = await copy_context_with(
            ctx, author=member, content=f"{ctx.prefix}{command_string}"
        )
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.invoke(alt_ctx)

    @Feature.Command(parent="jsk", name="sudo", aliases=["admin", "bypass"])
    async def jsk_sudo(self, ctx: Context, *, command_string):
        """
        Run a command, bypassing all checks.
        """
        alt_ctx = await copy_context_with(ctx, content=f"{ctx.prefix}{command_string}")
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.reinvoke(alt_ctx)

    @Feature.Command(parent="jsk", name="in", aliases=["channel", "inside"])
    async def jsk_in(self, ctx: Context, channel: discord.TextChannel, *, command_string):
        """
        Run a command in another channel.
        """
        alt_ctx = await copy_context_with(
            ctx, channel=channel, content=f"{ctx.prefix}{command_string}"
        )
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.invoke(alt_ctx)

    @Feature.Command(parent="jsk", name="tasks")
    async def jsk_tasks(self, ctx: Context):
        """
        Shows the currently running jishaku tasks.
        """
        if not self.tasks:
            return await ctx.send("No currently running tasks.")

        paginator = commands.Paginator(max_size=1985, prefix="", suffix="")

        for task in self.tasks:
            paginator.add_line(
                f"{task.index}: `{task.ctx.command.qualified_name}`, invoked at "
                f"{discord.utils.format_dt(task.ctx.message.created_at)} "
                f"({discord.utils.format_dt(task.ctx.message.created_at, 'R')})"
            )

        interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        return await interface.send_to(ctx)

    @Feature.Command(parent="jsk")
    async def news(self, ctx: Context, *, news: str):
        """
        Change the bot's current news.
        """
        with open("config.toml", "r") as afile:
            load = toml.loads(afile.read())
            load["news"]["news"] = news
        with open("config.toml", "w") as bfile:
            toml.dump(load, bfile)
            self.bot.news = news
        embed = discord.Embed(
            title="Successfully Set News.", description=f"Here is the preview.\n{news}"
        )
        await ctx.send(embed=embed)

    @Feature.Command(parent="jsk")
    async def ilreload(self, ctx: Context, module: str):
        """
        Reload a module using importlib.
        """
        try:
            m = importlib.reload(__import__(module))
            await ctx.send(f"Reloaded Sucessfully: `{m}`")
        except Exception as exc:
            await ctx.send(str(exc))

    @Feature.Command(parent="jsk", name="load", aliases=["l"])
    async def jsk_load(self, ctx: Context, *module: str):
        """
        Load cogs.
        """
        if module[0] in ["~", "*", "a", "all"]:
            await ctx.send("Loaded all extensions.")
            return await self.bot.load_extensions()
        load_list = []
        for cog in module:
            try:
                await self.bot.load_extension(cog)
                load_list.append(f'{self.bot.emoji_dictionary["green_tick"]} | {cog}')
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                load_list.append(
                    f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```'
                )
        embed = discord.Embed(title="Loaded cogs", description="\n".join(load_list))
        await ctx.send(embed=embed)

    @Feature.Command(parent="jsk", name="unload", aliases=["u"])
    async def jsk_unload(self, ctx: Context, module: CogConverter):
        """
        Unload cogs.
        """
        unload_list = []
        for cog in module:
            try:
                await self.bot.unload_extension(cog)
                unload_list.append(f'{self.bot.emoji_dictionary["green_tick"]} | {cog}')
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                unload_list.append(
                    f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```'
                )
        embed = discord.Embed(title="Unloaded cogs", description="\n".join(unload_list))
        await ctx.send(embed=embed)

    @Feature.Command(parent="jsk", name="reload", aliases=["r"])
    async def jsk_reload(self, ctx: Context, module: CogConverter):
        """
        Reload cogs.
        """
        reload_list = []
        for cog in module:
            try:
                await self.bot.reload_extension(cog)
                reload_list.append(f'{self.bot.emoji_dictionary["green_tick"]} | {cog}')
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                reload_list.append(
                    f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```'
                )
        description = "\n".join(reload_list)
        embed = discord.Embed(title="Reloaded Extensions", description=description)
        await ctx.send(embed=embed)

    @Feature.Command(parent="jsk", name="sync", aliases=["s"])
    async def jsk_sync(self, ctx: Context):
        """
        Pulls from GitHub then reloads all modules.

        If the command fails to unload, It will show the module and error.
        """
        sync_embed = discord.Embed(
            title="Syncing with GitHub", description="Please Wait..."
        )
        edit_sync = await ctx.send(embed=sync_embed)
        proc = await asyncio.create_subprocess_shell(
            "git pull", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if stdout:
            output = f"[stdout]\n{stdout.decode()}"
        elif stderr:
            output = f"[stderr]\n{stderr.decode()}"

        sync_embed.description = f"```bash\n{output}\n```"
        sync_embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        sync_embed.title = "Synced With GitHub"

        to_reload = [item.replace("/", ".").strip() for item in re.findall(r".*[^\/\n]+\.py", output, re.MULTILINE)]
        view = None
        if to_reload:
            sync_embed.set_footer(text="Reload Changed Files?")
            view = ReloadView(ctx, self.bot, to_reload, sync_embed)
        await edit_sync.edit(view=view, embed=sync_embed)

    @Feature.Command(parent="jsk", name="treesync", aliases=["ts", "synctree", "tsync", "stree"])
    async def jsk_tree_sync(self, ctx: commands.Context, *guild_ids: int):
        """
        Sync global or guild application commands to Discord.
        """

        paginator = WrappedPaginator(prefix='', suffix='')

        if not guild_ids:
            synced = await self.bot.tree.sync()
            paginator.add_line(f"\N{SATELLITE ANTENNA} Synced {len(synced)} global commands")
        else:
            for guild_id in guild_ids:
                try:
                    synced = await self.bot.tree.sync(guild=discord.Object(guild_id))
                except discord.HTTPException as exc:
                    paginator.add_line(f"\N{WARNING SIGN} `{guild_id}`: {exc.text}")
                else:
                    paginator.add_line(f"\N{SATELLITE ANTENNA} `{guild_id}` Synced {len(synced)} guild commands")

        for page in paginator.pages:
            await ctx.send(page)

    @Feature.Command(parent="jsk")
    async def leave(self, ctx: Context, guild: discord.Guild):
        """
        Command to leave a guild that may be abusing the bot.
        """
        conf = await ctx.confirm(
            f"Are you sure you want me to leave {guild.name} ({guild.id})?"
        )
        if conf.result:
            await guild.leave()
            return await ctx.message.add_reaction(
                self.bot.emoji_dictionary["green_tick"]
            )
        await conf.message.edit(content="Okay, Aborted.")

    @Feature.Command(parent="jsk", aliases=["bl"], invoke_without_command=True)
    async def blacklist(self, ctx: Context):
        """
        Show blacklisted users on the bot.
        """
        blacklist_ids = list(ctx.cache.blacklist.keys())
        source = BlacklistedPageSource(ctx, blacklist_ids)
        pages = Paginator(source, ctx=ctx, delete_message_after=True)
        await pages.start()

    @Feature.Command(parent="blacklist", name="add", aliases=["a"])
    async def blacklist_add(self, ctx: Context, user: discord.User, *, reason: ModReason = None):
        """
        Add a user to the global blacklist.
        """
        reason = reason or f"{ctx.author}: No reason provided."
        if user.id in self.bot.owner_ids:
            return await ctx.send("Can not blacklist that user.")
        blacklist_user = ctx.cache.blacklist.get(user.id)
        if blacklist_user:
            return await ctx.send(f"{user} is already blacklisted.")
        else:
            query = "INSERT INTO blacklist VALUES ($1, $2)"
            await self.bot.pool.execute(query, user.id, reason)
            ctx.cache.blacklist[user.id] = reason
            embed = discord.Embed(
                title="Updated Blacklist",
                description=f"Added {user} to the blacklist\nReason: `{reason}`"
            )
            await ctx.send(embed=embed)


    @Feature.Command(parent="blacklist", name="remove", aliases=["r"])
    async def blacklist_remove(self, ctx: Context, user: discord.User, *, reason: ModReason = None):
        """
        Removes a user from the global blacklist.
        """
        reason = reason or f"{ctx.author}: No reason provided."
        blacklist_user = ctx.cache.blacklist.get(user.id)
        if blacklist_user:
            query = "DELETE FROM blacklist WHERE user_id = $1"
            await self.bot.pool.execute(query, user.id)
            del ctx.cache.blacklist[user.id]
            embed = discord.Embed(
                title="Updated Blacklist",
                description=f"Removed {user} from the blacklist.\nReason: `{reason}`"
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{user} is not blacklisted.")

    @Feature.Command(parent="blacklist", name="update", aliases=["up"])
    async def blacklist_update(self, ctx: Context, user: discord.User, *, reason: ModReason):
        blacklist_user = ctx.cache.blacklist.get(user.id)
        if blacklist_user:
            query = "UPDATE blacklist SET reason = $2 WHERE user_id = $1"
            await self.bot.pool.execute(query, user.id, reason)
            ctx.cache.blacklist[user.id] = reason
            embed = discord.Embed(
                title="Updated Blacklist",
                description=f"Updated {user} blacklist reason.\nOld Reason: `{blacklist_user}`\nNew Reason: `{reason}`"
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{user} is not blacklisted.")

    @Feature.Command(parent="jsk")
    async def cleanup(self, ctx: Context, amount: int = 15):
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

    @Feature.Command(parent="jsk")
    async def maintenance(self, ctx: Context, toggle: bool):
        """
        Enables maintenance mode.

        When maintenance mode is enabled, The bot will only locked to devlopers.
        """
        match = {True: "enabled", False: "disabled"}
        self.bot.maintenance = toggle
        await ctx.send(f"Maintenance mode has been {match[toggle]}")

    @Feature.Command(parent="jsk", aliases=["cog", "extensions", "extension", "ext"])
    async def cogs(self, ctx: Context, cog: str = None):
        """
        Shows all the loaded cogs and how long ago they were loaded.
        """
        if cog:
            ext = self.bot.get_cog(cog)
            if not ext:
                return await ctx.send(f"{cog} does not exist.")
            return await ctx.send(f"{ext.qualified_name} | Loaded {discord.utils.format_dt(ext.load_time, 'R')}")
        thing_list = [
            f"{val.qualified_name} | Loaded {utils.timestamp(val.load_time, 'R')}"
            for _, val in self.bot.cogs.items()
        ]
        embed = discord.Embed(title="Loaded Cogs", description="\n".join(thing_list))
        await ctx.send(embed=embed)

    @Feature.Command(parent="jsk")
    async def guilds(self, ctx: Context):
        source = GuildPageSource(ctx, guilds=self.bot.guilds)
        pages = Paginator(source, ctx=ctx, disable_view_after=True)
        await pages.start()

    @Feature.Command(parent="jsk", invoke_without_command=True, aliases=["error"])
    async def errors(self, ctx: Context):
        """
        Show all the errors in the bot.
        """
        errors = await self.bot.pool.fetch(
            "SELECT * FROM command_errors WHERE fixed = False"
        )
        if not errors:
            embed = discord.Embed(
                title="Errors", description="No active errors have been found."
            )
            return await ctx.send(embed=embed)
        menu = Paginator(
            ErrorSource(ctx, errors, title="Unfixed errors", per_page=4),
            ctx=ctx,
            delete_message_after=True,
        )
        return await menu.start()

    @Feature.Command(parent="errors")
    async def fixed(self, ctx: Context):
        """
        Shows all fixed errors.
        """
        errors = await self.bot.pool.fetch(
            "SELECT * FROM command_errors WHERE fixed = True"
        )
        if not errors:
            embed = discord.Embed(
                title="Errors", description="No fixed errors have been found."
            )
            return await ctx.send(embed=embed)
        menu = Paginator(
            ErrorSource(ctx, errors, title="Fixed errors", per_page=4),
            ctx=ctx,
            delete_message_after=True,
        )
        return await menu.start()

    async def dm_error_trackers(self, data: dict):
        user_ids = data["trackers"]
        embed = discord.Embed(
            title=f"Error #{data['id']} fixed.",
            description=f"The error in command `{data['command']}` was marked as fixed."
        )
        for uid in user_ids:
            user = self.bot.get_user(uid)
            if user is not None:
                await user.send(embed=embed)
                await asyncio.sleep(1)

    @Feature.Command(parent="errors")
    async def fix(self, ctx: Context, *error_id: int):
        """
        Marks an error as fixed.

        Giving multiple IDs will mark all of them as fixed.
        """
        fix_list = []
        trackers = None
        for i in error_id:
            query = "SELECT * FROM command_errors WHERE id=$1"
            error_info = await self.bot.pool.fetchrow(query, i)
            if not error_info:
                fix_list.append(f"Error ID {i} does not exist.")
            elif error_info["fixed"] is True:
                fix_list.append(f"Error ID {i} is already marked as fixed.")
            else:
                query = "UPDATE command_errors SET fixed=$1 WHERE id=$2 RETURNING *"
                trackers = await self.bot.pool.fetchrow(query, True, i)
                fix_list.append(f"Error ID {i} has been marked as fixed.")
        await ctx.send("\n".join(fix_list))
        if trackers:
            await self.dm_error_trackers(trackers)

    @Feature.Command(
        parent="jsk",
        aliases=["dmsg", "dmessage", "delmsg", "deletem", "deletemsg", "delmessage"],
    )
    async def deletemessage(
        self, ctx: Context, message: discord.Message = None
    ):
        if message is None and ctx.reference is not None:
            if ctx.reference.author == ctx.me:
                await ctx.reference.delete()
            else:
                return await ctx.message.add_reaction(
                    self.bot.emoji_dictionary["red_tick"]
                )
        if message and message.author == ctx.me:
            await message.delete()
        return await ctx.message.add_reaction(self.bot.emoji_dictionary["green_tick"])
