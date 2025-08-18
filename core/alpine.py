"""
[Alpine Bot]
Copyright (C) 2021 - 2025 avizum

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
import logging
import re
from datetime import datetime
from typing import Any, Callable, ClassVar, Mapping, TYPE_CHECKING

import async_timeout
import discord
import jishaku
import mystbin
import toml
import wavelink
from aiohttp import ClientSession
from asyncdagpi.client import Client as DagpiClient
from asyncgist.client import Client as GistClient
from discord.ext import commands
from discord.utils import _ColourFormatter
from somerandomapi import Client as SRClient
from topgg.client import DBLClient
from topgg.webhook import WebhookManager

from utils import Database

from .core import Command, Group

if TYPE_CHECKING:
    from core import Cog, Context
    from extensions.listeners.errorhandler import ErrorHandler

__all__ = ("Bot",)

jishaku.Flags.HIDE = True
jishaku.Flags.NO_UNDERSCORE = True
jishaku.Flags.NO_DM_TRACEBACK = True


BOT_ID: int = 756257170521063444
BETA_BOT_ID: int = 787046145884291072
DEFAULT_PREFIXES: list[str] = ["a."]
BETA_PREFIXES: list[str] = ["b."]
OWNER_IDS: set[int] = {
    750135653638865017,
    547280209284562944,
    765098549099626507,
    756757268736901120,
}


_log = logging.getLogger("alpine")
handler = logging.StreamHandler()
handler.setFormatter(_ColourFormatter())
_log.setLevel(logging.INFO)
_log.addHandler(handler)
logging.getLogger("wavelink").addHandler(handler)


class Bot(commands.Bot):
    user: discord.ClientUser
    owner_ids: set[int]
    token: str
    launch_time: datetime = datetime.now(dt.timezone.utc)
    maintenance: bool = False
    commands_ran: int = 0
    command_usage: ClassVar[dict[str, int]] = {}
    command_cache: ClassVar[dict[int, discord.Message]] = {}
    invite: str = discord.utils.oauth_url(BOT_ID, permissions=discord.Permissions(8))
    support: str = "https://discord.gg/hWhGQ4QHE9"
    source: str = "https://github.com/avizum/alpine"
    context: type[commands.Context] | None = None
    cogs: Mapping[str, Cog]

    to_load: tuple[str, ...] = (
        "core.context",
        "extensions.cogs.botinfo",
        "extensions.cogs.fun",
        "extensions.cogs.games",
        "extensions.cogs.help",
        "extensions.cogs.highlight",
        "extensions.cogs.images",
        "extensions.cogs.meta",
        "extensions.cogs.moderation",
        "extensions.cogs.music",
        "extensions.cogs.owner",
        "extensions.cogs.servermanagement",
        "extensions.cogs.settings",
        "extensions.cogs.support",
        "extensions.cogs.verification",
        "extensions.extras.setup",
        "extensions.extras.topgg",
        "extensions.listeners.errorhandler",
        "extensions.listeners.events",
        "extensions.listeners.joins_and_leaves",
    )

    with open("config.toml") as config:
        settings = toml.loads(config.read())
    api: dict[str, str] = settings["api_tokens"]
    news: str = settings["news"]["news"]

    allowed_mentions: discord.AllowedMentions = discord.AllowedMentions.none()
    activity: discord.CustomActivity = discord.CustomActivity(name="Loading...")

    intents: discord.Intents = discord.Intents(
        bans=True,
        emojis=True,
        guilds=True,
        messages=True,
        members=True,
        presences=True,
        reactions=True,
        webhooks=True,
        voice_states=True,
        message_content=True,
    )

    def __init__(self) -> None:
        super().__init__(
            command_prefix=self.__class__.get_prefix,
            case_insensitive=True,
            strip_after_prefix=True,
            allowed_mentions=self.allowed_mentions,
            activity=self.activity,
            intents=self.intents,
            status=discord.Status.idle,
            chunk_guilds_at_startup=True,
            max_messages=5000,
            owner_ids=OWNER_IDS,
        )
        self.token: str
        self._BotBase__cogs: dict[str, Cog] = commands.core._CaseInsensitiveDict()

    def __repr__(self) -> str:
        return (
            f"<Bot id={self.user.id} name={self.user.name!r} "
            f"discriminator={self.user.discriminator!r} bot={self.user.bot}>"
        )

    def __str__(self) -> str:
        return str(self.user)

    def __int__(self) -> int:
        self._connection
        return self.user.id

    async def setup_hook(self) -> None:
        self.session: ClientSession = ClientSession()
        self.database: Database = Database(self)
        self.topgg: DBLClient = DBLClient(self, self.api["TopGG"], autopost_interval=None, session=self.session)
        self.topgg_webhook: WebhookManager = WebhookManager(self).dbl_webhook("/dbl", self.api["TopGGWH"])
        self.gist: GistClient = GistClient(self.api["GitHub"], self.session)
        self.sr: SRClient = SRClient()
        self.dagpi: DagpiClient = DagpiClient(self.api["DagpiAPI"], session=self.session)
        self.myst: mystbin.Client = mystbin.Client(session=self.session)
        self.loop.create_task(self.load_extensions())
        self.loop.create_task(self.start_nodes())
        self.loop.create_task(self.find_restart_message())
        self.topgg_webhook.run(8025)

    async def get_prefix(self, message: discord.Message) -> list[str]:
        base: list[str] = [f"<@{self.user.id}>", f"<@!{self.user.id}>"]

        if BOT_ID == BETA_BOT_ID:
            base.extend(BETA_PREFIXES)
            return base

        if message.guild:
            guild_settings = self.database.get_guild(message.guild.id)
            if not guild_settings or (guild_settings and not guild_settings.prefixes):
                base.extend(DEFAULT_PREFIXES)
            else:
                base.extend(guild_settings.prefixes)
        else:
            base.extend(DEFAULT_PREFIXES)
        prefixes = "|".join(map(re.escape, base))

        match = re.match(rf"^({prefixes}\s*).*", message.content, flags=re.IGNORECASE)
        if match:
            base.append(match[1])
        return base

    async def load_extensions(self) -> None:
        for ext in self.to_load:
            try:
                await self.load_extension(ext)
                _log.info(f"Loaded extension: {ext}")
            except commands.ExtensionError as error:
                _log.error(f"Exception in loading extension {ext}:", exc_info=error)

    async def find_restart_message(self) -> None:
        await self.wait_until_ready()
        with open("reboot.toml", "r+") as f:  # noqa: ASYNC230  # This operation only happens when the bot is starting.
            info = toml.loads(f.read())
            if info:
                channel = self.get_channel(info["channel_id"])
                if channel is not None and isinstance(channel, discord.TextChannel):
                    message = channel.get_partial_message(info["message_id"])
                    if message:
                        now: datetime = datetime.now(tz=dt.timezone.utc)
                        await message.edit(content=f"Took {(now - info['restart_time']).seconds} seconds to restart.")
                    f.truncate(0)
                f.close()

    async def start_nodes(self) -> None:
        await self.wait_until_ready()

        nodes = [wavelink.Node(**self.settings["lavalink"])]
        try:
            async with async_timeout.timeout(15):
                await wavelink.Pool.connect(nodes=nodes, client=self)
                _log.info("Connected to Lavalink node. ")

        except asyncio.TimeoutError as timed_out:
            extension = "extensions.cogs.music"
            error_handler: ErrorHandler | None = self.get_cog("errorhandler")  # type: ignore
            message = f"Could not connect to Lavalink node within 15 seconds. Unloaded {extension}"
            if error_handler:
                await error_handler.error_webhook.send(message)
            await self.unload_extension(extension)

            _log.error(message, exc_info=timed_out)

    async def on_ready(self) -> None:
        _log.info(f"Running: {self.user.name} ({self.user.id})")

    async def wait_for(
        self,
        event: str,
        *,
        check: Callable[..., bool] | None = None,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> Any:
        if event == "message":

            def bl_message_check(*args: Any) -> bool:
                can_run = self.database.get_blacklist(args[0].author.id) is None
                if check:
                    return can_run and check(*args)
                return can_run

            return await super().wait_for(event, check=bl_message_check, timeout=timeout)

        if event in {"reaction_add", "reaction_remove"}:

            def bl_reaction_check(*args) -> bool:
                can_run = self.database.get_blacklist(args[1].id) is None
                if check:
                    return can_run and check(*args)
                return not can_run

            return await super().wait_for(event, check=bl_reaction_check, timeout=timeout)

        bl_check = check
        return await super().wait_for(event, check=bl_check, timeout=timeout)

    async def get_context(
        self,
        origin: discord.Message | discord.Interaction,
        *,
        cls: Context | None = None,
    ) -> Context:
        return await super().get_context(origin, cls=cls or self.context)  # type: ignore

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.content == after.content or after.attachments:
            return
        await self.process_commands(after)

    async def on_message_delete(self, message: discord.Message) -> None:
        if message.id in self.command_cache:
            await self.command_cache[message.id].delete(delay=0)
            self.command_cache.pop(message.id, None)

    async def is_owner(self, user: discord.User | discord.Member, /) -> bool:
        return user.id in self.owner_ids

    def command(self, name=None, cls=None, **kwargs):
        if cls is None:
            cls = Command

        def decorator(func):
            if isinstance(func, Command):
                raise TypeError("Callback is already a command")
            res = cls(func, name=name, **kwargs)
            self.add_command(res)
            return res

        return decorator

    def group(self, name=None, **kwargs):
        return self.command(name=name, cls=Group, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> None:
        if not self.token:
            raise TypeError(f"Bot.token expected to be str, recieved {self.token.__class__.__name__} instead")
        super().run(self.token, *args, **kwargs, reconnect=True)

    async def close(self) -> None:
        await self.session.close()
        await self.sr.close()

        # Cope
        for view in list(self._connection._view_store._synced_message_views.values()):
            if view.is_finished():
                continue
            try:
                message: discord.Message = getattr(view, "message")
                delete_after: bool = getattr(view, "delete_message_after")
                remove_after: bool = getattr(view, "remove_view_after")
                disable_after: bool = getattr(view, "disable_view_after")
                if delete_after:
                    await message.delete()
                if remove_after:
                    await message.edit(view=None)
                if disable_after:
                    getattr(view, "disable_all")()
                    await message.edit(view=view)  # type: ignore
                view.stop()
            except (AttributeError, discord.NotFound):
                pass

        _log.info(f"Stopped: {self.user.name} ({self.user.id})")
        await super().close()
