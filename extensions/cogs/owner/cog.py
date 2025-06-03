"""
[Alpine Bot]
Copyright (C) 2021 - 2024 avizum

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
import contextlib
import datetime
import importlib
import inspect
import io
import math
import re
import sys
import traceback
from difflib import get_close_matches
from importlib.metadata import distribution, packages_distributions
from types import TracebackType
from typing import Any, Callable, Deque, Generator, TYPE_CHECKING

import discord
import psutil
import toml
from asyncpg import Record
from discord.ext import commands, menus
from jishaku import exception_handling, Feature
from jishaku.codeblocks import Codeblock, codeblock_converter
from jishaku.cog import OPTIONAL_FEATURES, STANDARD_FEATURES
from jishaku.exception_handling import ReplResponseReactor
from jishaku.functools import AsyncSender
from jishaku.models import copy_context_with
from jishaku.modules import package_version
from jishaku.paginators import PaginatorInterface
from jishaku.repl import AsyncCodeExecutor

import core
from utils import DefaultReason, Emojis, ModReason, Paginator, PaginatorEmbed, timestamp, View

if TYPE_CHECKING:
    from jishaku.features.baseclass import CommandTask
    from jishaku.repl import Scope

    from core import Bot, Context
    from extensions.cogs.moderation import Moderation


def natural_size(size_in_bytes: int) -> str:
    """
    Converts a number of bytes to an appropriately-scaled unit
    E.g.:
        1024 -> 1.00 KiB
        12345678 -> 11.77 MiB
    """
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")

    power = int(math.log(size_in_bytes, 1024))

    return f"{size_in_bytes / (1024 ** power):.2f} {units[power]}"


async def _send_traceback(
    destination: discord.abc.Messageable | discord.Message,
    verbosity: int,
    etype: type[BaseException],
    value: BaseException,
    trace: TracebackType,
):
    """
    Sends a traceback of an exception to a destination.
    Used when REPL fails for any reason.
    :param destination: Where to send this information to
    :param verbosity: How far back this traceback should go. 0 shows just the last stack.
    :param exc_info: Information about this exception, from sys.exc_info or similar.
    :return: The last message sent
    """

    traceback_content = "".join(traceback.format_exception(etype, value, trace, verbosity)).replace("``", "`\u200b`")

    paginator = commands.Paginator(prefix="```py")
    for line in traceback_content.split("\n"):
        tb_line = line.replace(str(destination._state.http.token), "[token omitted]")
        for i in sys.path:
            tb_line = line.replace(i, ".")
        paginator.add_line(tb_line)

    message = None

    for page in paginator.pages:
        if isinstance(destination, discord.abc.Messageable):
            message = await destination.send(page)
        else:
            message = await destination.reply(page)

    return message


exception_handling.send_traceback = _send_traceback


class CogConverter(commands.Converter, list):
    async def convert(self, ctx: Context, argument: str) -> list[str]:
        exts = []
        if argument in {"~", "*", "a", "all"}:
            exts.extend(ctx.bot.extensions)
        elif argument not in ctx.bot.extensions:
            arg = get_close_matches(argument, ctx.bot.extensions)
            if arg:
                exts.append(arg[0])
        else:
            exts.append(argument)
        return exts


class ErrorSource(menus.ListPageSource):
    def __init__(
        self,
        ctx: Context,
        errors: list[Record],
        *,
        title: str = "Errors",
        per_page: int = 1,
    ) -> None:
        super().__init__(entries=errors, per_page=per_page)
        self.ctx = ctx
        self.title = title

    async def format_page(self, menu: menus.Menu, page: list[Record]) -> discord.Embed:
        embed = discord.Embed(title=self.title, color=await self.ctx.fetch_color())
        for error in page:
            embed.add_field(
                name=f"{error['command']} | `{error['id']}`",
                value=f"```\n{error['error']}```",
                inline=False,
            )
        return embed


class GuildPageSource(menus.ListPageSource):
    def __init__(self, ctx: Context, guilds: list[discord.Guild]) -> None:
        self.ctx = ctx
        super().__init__(guilds, per_page=2)

    async def format_page(self, menu: menus.Menu, page: list[discord.Guild]) -> discord.Embed:
        embed = PaginatorEmbed(ctx=self.ctx)
        for guild in page:
            assert guild.me.joined_at is not None
            embed.add_field(
                name=guild.name,
                value=(
                    f"Owner: {guild.owner}\n"
                    f"Members: {guild.member_count}\n"
                    f"Created at: {timestamp(guild.created_at)}\n"
                    f"Joined at: {timestamp(guild.me.joined_at)}"
                ),
                inline=False,
            )
        return embed


class BlacklistedPageSource(menus.ListPageSource):
    def __init__(self, ctx: Context, blacklisted: list[int]) -> None:
        self.ctx = ctx
        super().__init__(blacklisted, per_page=2)

    async def format_page(self, menu: menus.Menu, page: list[int]) -> discord.Embed:
        embed = PaginatorEmbed(ctx=self.ctx, title="Blacklisted Users")
        for entry in page:
            user = self.ctx.bot.get_user(entry)
            bl_entry = self.ctx.database._blacklists[entry]
            embed.add_field(
                name=f"{user}({user.id})" if user else entry,
                value=f"[Reason]\n{bl_entry}",
                inline=False,
            )
        return embed


class ReloadView(View):
    def __init__(self, ctx: Context, bot: Bot, to_reload: list[str], embed: discord.Embed) -> None:
        self.ctx = ctx
        self.bot = bot
        self.embed = embed
        self.to_reload: list[str] | None = None
        self.get_close_cogs(to_reload)
        super().__init__(member=self.ctx.author, timeout=60)

    def get_close_cogs(self, argument: list[str]):
        self.to_reload = [get_close_matches(cog, self.bot.extensions)[0] for cog in argument]

    @discord.ui.button(label="Reload", style=discord.ButtonStyle.blurple)
    async def reload_modules(self, interaction: discord.Interaction, button: discord.ui.Button):
        reload_list = []
        if not self.to_reload:
            return await interaction.response.send_message("No cogs to reload.")
        for cog in self.to_reload:
            try:
                await self.bot.reload_extension(cog)
                reload_list.append(f"{Emojis.GREEN_TICK} | {cog}")
            except commands.ExtensionError as e:
                reload_list.append(f"{Emojis.RED_TICK} | {cog}\n```{e}```")
        if not reload_list:
            self.embed.add_field(name="Reloaded Modules", value="No modules were reloaded")
        else:
            self.embed.add_field(name="Reloaded Modules", value="\n".join(reload_list))
        self.embed.set_footer()
        await interaction.response.edit_message(embed=self.embed, view=None)
        return self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray)
    async def cancel_reload(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view=None)
        self.stop()


FILE_REGEX = re.compile(r"^(.*[^/\n]+)(\.py)")


class Owner(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    tasks: Deque[CommandTask]
    jsk_python_result_handling: Callable[[Context, Any], Any]
    jsk_python_get_convertables: Callable[[Context], tuple[dict[str, Any], dict[str, str]]]
    submit: Callable[[Context], Any]
    walk_commands: Callable[[], Generator[core.Command[Any, ..., Any], None, None]]
    load_time: datetime.datetime
    start_time: datetime.datetime
    scope: Scope

    """
    Advanced debug cog for bot Developers.
    """

    def __init__(self, bot: Bot, **kwargs) -> None:
        self.emoji = "<:jishaku:913256121542791178>"
        self.bot = bot
        super().__init__(bot=bot, **kwargs)  # type: ignore
        for i in self.walk_commands():
            i.member_permissions = ["Bot Owner"]

    @core.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member) -> None:
        waste = "\U0001f5d1\U0000fe0f"
        if reaction.emoji == waste and await self.bot.is_owner(user) and reaction.message.author == self.bot.user:
            await reaction.message.delete()

    @Feature.Command(
        name="jishaku",
        aliases=["jsk", "dev", "developer"],
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

        # Try to locate what vends the `discord` package
        distributions: list[str] = [
            dist
            for dist in packages_distributions()["discord"]
            if any(file.parts == ("discord", "__init__.py") for file in distribution(dist).files)  # type: ignore
        ]

        if distributions:
            dist_version = f"{distributions[0]} `{package_version(distributions[0])}`"
        else:
            dist_version = f"unknown `{discord.__version__}`"

        summary = [
            f"Jishaku v{package_version('jishaku')}, {dist_version}, "
            f"`Python {sys.version}` on `{sys.platform}`".replace("\n", ""),
            f"Module was loaded <t:{self.load_time.timestamp():.0f}:R>, "
            f"cog was loaded <t:{self.start_time.timestamp():.0f}:R>.",
            "",
        ]

        try:
            proc = psutil.Process()

            with proc.oneshot():
                try:
                    mem = proc.memory_full_info()
                    summary.append(
                        f"Using {natural_size(mem.rss)} physical memory and "
                        f"{natural_size(mem.vms)} virtual memory, "
                        f"{natural_size(mem.uss)} of which unique to this process."
                    )
                except psutil.AccessDenied:
                    pass

                try:
                    name = proc.name()
                    pid = proc.pid
                    thread_count = proc.num_threads()

                    summary.append(f"Running on PID {pid} (`{name}`) with {thread_count} thread(s).")
                except psutil.AccessDenied:
                    pass

                summary.append("")  # blank line
        except psutil.AccessDenied:
            summary.append(
                "psutil is installed, but this process does not have high enough access rights "
                "to query process information."
            )
            summary.append("")  # blank line

        guilds = f"{len(self.bot.guilds):,} guilds"
        humans = f"{sum(not m.bot for m in self.bot.users):,} humans"
        bots = f"{sum(m.bot for m in self.bot.users):,} bots"
        users = f"{len(self.bot.users):,} users"
        cache_summary = f"{guilds} and can see {humans}, and {bots}, totalling to {users}"

        # Show shard settings to summary
        if isinstance(self.bot, discord.AutoShardedClient):
            if len(self.bot.shards) > 20:
                summary.append(
                    f"This bot is automatically sharded ({len(self.bot.shards)} shards of {self.bot.shard_count})"
                    f" and can see {cache_summary}."
                )
            else:
                shard_ids = ", ".join(str(i) for i in self.bot.shards)
                summary.append(
                    f"This bot is automatically sharded (Shards {shard_ids} of {self.bot.shard_count})"
                    f" and can see {cache_summary}."
                )
        elif self.bot.shard_count:
            summary.append(
                f"This bot is manually sharded (Shard {self.bot.shard_id} of {self.bot.shard_count})"
                f" and can see {cache_summary}."
            )
        else:
            summary.append(f"This bot is not sharded and can see {cache_summary}.")

        if self.bot._connection.max_messages:
            message_cache = f"Message cache capped at {self.bot._connection.max_messages}"
        else:
            message_cache = "Message cache is disabled"

        remarks = {True: "`enabled`", False: "`disabled`", None: "`unknown`"}

        *group, last = (
            f"{intent.replace('_', ' ')} intent is {remarks.get(getattr(self.bot.intents, intent, None))}"
            for intent in ("presences", "members", "message_content")
        )

        summary.append(f"{message_cache}, {', '.join(group)}, and {last}.")

        # Show websocket latency in milliseconds
        summary.append(f"Average websocket latency: `{round(self.bot.latency * 1000, 2)}ms`")

        embed = discord.Embed(description="\n".join(summary))
        await ctx.send(embed=embed)

    @Feature.Command(parent="jsk", name="py", aliases=["python"])
    async def jsk_python(self, ctx: Context, *, argument: codeblock_converter):  # type: ignore
        """
        Direct evaluation of Python code.
        """
        arg_dict, convertables = self.jsk_python_get_convertables(ctx)
        message_reference = getattr(ctx.message.reference, "resolved", None)
        voice_client = ctx.voice_client
        arg_dict["reference"] = message_reference
        arg_dict["ref"] = message_reference
        arg_dict["core"] = core
        arg_dict["source"] = inspect.getsource
        arg_dict["vc"] = voice_client
        arg_dict["player"] = voice_client
        arg_dict["_"] = self.last_result

        out = io.StringIO()
        scope = self.scope

        try:
            async with ReplResponseReactor(ctx.message):
                with contextlib.redirect_stdout(out):
                    with self.submit(ctx):
                        executor = AsyncCodeExecutor(argument.content, scope, arg_dict=arg_dict, convertables=convertables)
                        async for send, result in AsyncSender(executor):  # type: ignore
                            send: Callable[..., None]
                            result: Any

                            if result is None and out and out.getvalue():
                                redirected = f"Redirected stdout\n{ctx.codeblock(out.getvalue())}"
                                self.last_result = redirected
                                send(await self.jsk_python_result_handling(ctx, redirected))
                                continue

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
            with open("reboot.toml", "w") as f:  # noqa: ASYNC230  # This function stops the bot, async doesn't matter
                toml.dump(
                    {
                        "message_id": conf.message.id,
                        "channel_id": ctx.channel.id,
                        "restart_time": datetime.datetime.now(tz=datetime.timezone.utc),
                    },
                    f,
                )
            await conf.message.edit(content="Rebooting...", embed=None, view=None)
            await self.bot.close()
        else:
            await conf.message.edit(content="Reboot aborted", embed=None, delete_after=5)

    @Feature.Command(parent="jsk", name="su")
    async def jsk_su(self, ctx: Context, member: discord.Member, *, command_string: str):
        """
        Run a command as someone else.
        """
        alt_ctx = await copy_context_with(ctx, author=member, content=f"{ctx.prefix}{command_string}")
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.invoke(alt_ctx)

    @Feature.Command(parent="jsk", name="sudo", aliases=["admin", "bypass"])
    async def jsk_sudo(self, ctx: Context, *, command_string: str):
        """
        Run a command, bypassing all checks.
        """
        alt_ctx = await copy_context_with(ctx, content=f"{ctx.prefix}{command_string}")
        if alt_ctx.command is None:
            return await ctx.send(f'Command "{alt_ctx.invoked_with}" does not exist.')
        return await alt_ctx.command.reinvoke(alt_ctx)

    @Feature.Command(parent="jsk", name="in", aliases=["channel", "inside"])
    async def jsk_in(self, ctx: Context, channel: discord.TextChannel, *, command_string: str):
        """
        Run a command in another channel.
        """
        alt_ctx = await copy_context_with(ctx, channel=channel, content=f"{ctx.prefix}{command_string}")
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
            if task.ctx.command:
                paginator.add_line(
                    f"{task.index}: `{task.ctx.command.qualified_name}`, invoked at "
                    f"{timestamp(task.ctx.message.created_at)} "
                    f"({timestamp(task.ctx.message.created_at):R})"
                )
            else:
                paginator.add_line(
                    f"{task.index}: unknown, invoked at "
                    f"{timestamp(task.ctx.message.created_at)} "
                    f"({timestamp(task.ctx.message.created_at):R})"
                )

        interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        return await interface.send_to(ctx)

    @Feature.Command(parent="jsk")
    async def news(self, ctx: Context, *, news: str):
        """
        Change the bot's current news.
        """
        with open("config.toml", "r+") as news_file:  # noqa: ASYNC230  # The time it blocks is negligible
            load = toml.loads(news_file.read())
            load["news"]["news"] = news
            news_file.seek(0)
            news_file.truncate()
            toml.dump(load, news_file)
            self.bot.news = news
        embed = discord.Embed(title="Successfully Set News.", description=f"Here is the preview.\n{news}")
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
    async def jsk_load(self, ctx: Context, module: str):
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
                load_list.append(f"{Emojis.GREEN_TICK} | {cog}")
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                load_list.append(f"{Emojis.RED_TICK} | {cog}```{e}```")
        embed = discord.Embed(title="Loaded cogs", description="\n".join(load_list))
        return await ctx.send(embed=embed)

    @Feature.Command(parent="jsk", name="unload", aliases=["u"])
    async def jsk_unload(self, ctx: Context, module: CogConverter):
        """
        Unload cogs.
        """
        unload_list = []
        for cog in module:
            try:
                await self.bot.unload_extension(cog)
                unload_list.append(f"{Emojis.GREEN_TICK} | {cog}")
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                unload_list.append(f"{Emojis.RED_TICK} | {cog}```{e}```")
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
                reload_list.append(f"{Emojis.GREEN_TICK} | {cog}")
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                reload_list.append(f"{Emojis.RED_TICK} | {cog}```{e}```")
        description = "\n".join(reload_list)
        embed = discord.Embed(title="Reloaded Extensions", description=description)
        await ctx.send(embed=embed)

    @Feature.Command(parent="jsk", name="git", invoke_without_command=True)
    async def jsk_git(self, ctx: Context, argument: codeblock_converter):  # type: ignore
        """
        Shortcut for `jsk git sh`.
        """
        return await ctx.invoke(
            self.jsk_shell, argument=Codeblock(argument.language, "git " + argument.content)  # type: ignore
        )

    @Feature.Command(parent="jsk_git", name="sync")
    async def jsk_git_sync(self, ctx: Context):
        """
        Pulls from GitHub then reloads all modules.

        If the command fails to unload, It will show the module and error.
        """
        sync_embed = discord.Embed(title="Syncing with GitHub", description="Please Wait...")
        edit_sync = await ctx.send(embed=sync_embed)
        proc = await asyncio.create_subprocess_shell(
            "git pull", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        output = "Something went wrong if you can see this.\n"

        if stdout:
            output = f"[stdout]\n{stdout.decode()}"
        elif stderr:
            output = f"[stderr]\n{stderr.decode()}"

        sync_embed.description = f"```bash\n{output}\n```"
        sync_embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        sync_embed.title = "Synced With GitHub"

        to_reload = None or [item.replace("/", ".").strip() for item in re.findall(r".*[^\/\n]+\.py", output, re.MULTILINE)]
        view = None
        if to_reload:
            sync_embed.set_footer(text="Reload changed files?")
            view = ReloadView(ctx, self.bot, to_reload, sync_embed)
        await edit_sync.edit(view=view, embed=sync_embed)

    @Feature.Command(parent="jsk")
    async def leave(self, ctx: Context, guild: discord.Guild):
        """
        Command to leave a guild that may be abusing the bot.
        """
        conf = await ctx.confirm(message=f"Are you sure you want me to leave {guild.name} ({guild.id})?")
        if conf.result:
            await guild.leave()
            return await ctx.message.add_reaction(Emojis.GREEN_TICK)
        return await conf.message.edit(content="Okay, Aborted.")

    @Feature.Command(parent="jsk", aliases=["bl"], invoke_without_command=True)
    async def blacklist(self, ctx: Context):
        """
        Show blacklisted users on the bot.
        """
        blacklist_ids = list(ctx.database._blacklists.keys())
        source = BlacklistedPageSource(ctx, blacklist_ids)
        pages = Paginator(source, ctx=ctx, delete_message_after=True)
        await pages.start()

    @Feature.Command(parent="blacklist", name="add", aliases=["a"])
    async def blacklist_add(self, ctx: Context, user: discord.User, *, reason: ModReason = DefaultReason):
        """
        Add a user to the global blacklist.
        """
        if user.id in self.bot.owner_ids:
            return await ctx.send("Can not blacklist that user.")

        to_blacklist = ctx.database.get_blacklist(user.id)
        if to_blacklist:
            return await ctx.send(f"{user} is already blacklisted.")

        await ctx.database.blacklist(user.id, reason=reason.blacklist)
        fmt = reason.replace("|\u200b|", ": ")
        embed = discord.Embed(
            title="Updated Blacklist",
            description=f"Added {user} to the blacklist\nReason: `{fmt}`",
        )
        return await ctx.send(embed=embed)

    @Feature.Command(parent="blacklist", name="remove", aliases=["r"])
    async def blacklist_remove(self, ctx: Context, user: discord.User):
        """
        Removes a user from the global blacklist.
        """
        to_unblacklist = ctx.database.get_blacklist(user.id)
        if not to_unblacklist:
            return await ctx.send(f"{user} is not blacklisted.")

        await to_unblacklist.delete()
        return await ctx.send(f"Removed {user} from the blacklist.")

    @Feature.Command(parent="jsk")
    async def cleanup(self, ctx: Context, amount: int = 15):
        """
        Delete only the bot messages.

        Goes through channel history and then deletes them one by one.
        """

        def check(m: discord.Message):
            return m.author == self.bot.user

        perms = ctx.bot_permissions.manage_messages
        purged = await ctx.channel.purge(limit=amount, check=check, bulk=perms)
        cog: Moderation | None = self.bot.get_cog("moderation")  # type: ignore
        if cog is None:
            return await ctx.send(f"{len(purged)} messages deleted.")
        return await ctx.can_delete(embed=await cog._affected(purged))

    @Feature.Command(parent="jsk")
    async def maintenance(self, ctx: Context, toggle: bool):
        """
        Enables maintenance mode.

        When maintenance mode is enabled, The bot will only locked to devlopers.
        """
        match = {True: "enabled", False: "disabled"}
        self.bot.maintenance = toggle
        self.bot.extra_events = {}
        await ctx.send(f"Maintenance mode has been {match[toggle]}")

    @Feature.Command(parent="jsk", aliases=["cog", "extensions", "extension", "ext"])
    async def cogs(self, ctx: Context, cog: str | None = None):
        """
        Shows all the loaded cogs and how long ago they were loaded.
        """
        if cog:
            ext: core.Cog | None = self.bot.get_cog(cog)  # type: ignore
            if not ext:
                return await ctx.send(f"{cog} does not exist.")
            return await ctx.send(f"{ext.qualified_name} | Loaded {timestamp(ext.load_time):R}")
        thing_list = [f"{val.qualified_name} | Loaded {timestamp(val.load_time):R}" for _, val in self.bot.cogs.items()]
        embed = discord.Embed(title="Loaded Cogs", description="\n".join(thing_list))
        return await ctx.send(embed=embed)

    @Feature.Command(parent="jsk")
    async def guilds(self, ctx: Context):
        source = GuildPageSource(ctx, guilds=list(self.bot.guilds))
        pages = Paginator(source, ctx=ctx, disable_view_after=True)
        await pages.start()

    @Feature.Command(parent="jsk", invoke_without_command=True, aliases=["error"])
    async def errors(self, ctx: Context):
        """
        Show all the errors in the bot.
        """
        errors = await ctx.database.pool.fetch("SELECT * FROM command_errors WHERE fixed = False")
        if not errors:
            embed = discord.Embed(title="Errors", description="No active errors have been found.")
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
        errors = await ctx.database.pool.fetch("SELECT * FROM command_errors WHERE fixed = True")
        if not errors:
            embed = discord.Embed(title="Errors", description="No fixed errors have been found.")
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
            description=f"The error in command `{data['command']}` was marked as fixed.",
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
        for _id in error_id:
            query = "SELECT * FROM command_errors WHERE id=$1"
            error_info = await ctx.database.pool.fetchrow(query, _id)
            if not error_info:
                fix_list.append(f"Error ID {_id} does not exist.")
            elif error_info["fixed"] is True:
                fix_list.append(f"Error ID {_id} is already marked as fixed.")
            else:
                query = "UPDATE command_errors SET fixed=$1, trackers=$2 WHERE id=$3 RETURNING *"
                trackers = await ctx.database.pool.fetchrow(query, True, [], _id)
                fix_list.append(f"Error ID {_id} has been marked as fixed.")
        await ctx.send("\n".join(fix_list))
        if trackers:
            await self.dm_error_trackers(trackers)

    @Feature.Command(
        parent="jsk",
        aliases=["dmsg", "dmessage", "delmsg", "deletem", "deletemsg", "delmessage"],
    )
    async def deletemessage(self, ctx: Context, message: discord.Message | None = None):
        if message is None and ctx.reference is not None:
            if ctx.reference.author == ctx.me:
                await ctx.reference.delete()
            else:
                return await ctx.message.add_reaction(Emojis.RED_TICK)
        if message and message.author == ctx.me:
            await message.delete()
        return await ctx.message.add_reaction(Emojis.GREEN_TICK)
