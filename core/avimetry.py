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

import datetime as dt
import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Any

import asyncpg
import discord
import jishaku
import mystbin
import toml
import wavelink
from asyncgist.client import Client as GistClient
from sr_api.client import Client as SRClient
from asyncdagpi.client import Client as DagpiClient
from aiohttp import ClientSession
from discord.ext import commands
from discord.client import _ColourFormatter
from wavelink.ext import spotify
from topgg.client import DBLClient
from topgg.webhook import WebhookManager

from core import Command, Group
from utils.cache import Cache

if TYPE_CHECKING:
    from .context import Context
    from extensions.listeners.errorhandler import ErrorHandler


jishaku.Flags.HIDE = True
jishaku.Flags.NO_UNDERSCORE = True
jishaku.Flags.NO_DM_TRACEBACK = True


DEFAULT_PREFIXES: list[str] = ["a.", "avimetry"]
BETA_PREFIXES: list[str] = ["ab.", "ba."]
OWNER_IDS: set[int] = {
    750135653638865017,
    547280209284562944,
    765098549099626507,
    756757268736901120,
}
PUBLIC_BOT_ID: int = 756257170521063444
BETA_BOT_ID: int = 787046145884291072


_log = logging.getLogger("avimetry")
handler = logging.StreamHandler()
handler.setFormatter(_ColourFormatter())
_log.setLevel(logging.INFO)
_log.addHandler(handler)


class Bot(commands.Bot):
    user: discord.ClientUser
    owner_ids: set[int]
    bot_id: int = PUBLIC_BOT_ID
    launch_time: datetime = datetime.now(dt.timezone.utc)
    maintenance: bool = False
    commands_ran: int = 0
    command_usage: dict[str, int] = {}
    command_cache: dict[int, discord.Message] = {}
    invite: str = discord.utils.oauth_url(bot_id, permissions=discord.Permissions(8))
    support: str = "https://discord.gg/muTVFgDvKf"
    source: str = "https://github.com/avimetry/avimetry"
    context: Context | None = None

    to_load: tuple[str, ...] = (
        "extensions.listeners.events",
        "extensions.cogs.owner",
        "extensions.extras.setup",
        "core.context",
        "extensions.cogs.animals",
        "extensions.cogs.botinfo",
        "extensions.listeners.errorhandler",
        "extensions.cogs.fun",
        "extensions.cogs.games",
        "extensions.cogs.help",
        "extensions.cogs.images",
        "extensions.listeners.joinsandleaves",
        "extensions.cogs.meta",
        "extensions.cogs.moderation",
        "extensions.cogs.music",
        "extensions.cogs.servermanagement",
        "extensions.cogs.settings",
        "extensions.extras.supportserver",
        "extensions.extras.topgg",
        "extensions.cogs.verification",
    )

    with open("config.toml") as token:
        settings = toml.loads(token.read())
    api: dict[str, str] = settings["api_tokens"]
    news: str = settings["news"]["news"]

    allowed_mentions: discord.AllowedMentions = discord.AllowedMentions.none()
    activity: discord.Game = discord.Game("Loading...")

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
        self._BotBase__cogs: dict[str, commands.Cog] = commands.core._CaseInsensitiveDict()

    def __repr__(self) -> str:
        return f"<Bot id={self.user.id}, name={self.user.discriminator}, discriminator={self.user.discriminator}>"

    async def setup_hook(self) -> None:
        self.session: ClientSession = ClientSession()
        self.cache: Cache = Cache(self)
        self.pool: asyncpg.Pool | None = await asyncpg.create_pool(**self.settings["postgresql"])
        self.topgg: DBLClient = DBLClient(self, self.api["TopGG"], autopost_interval=None, session=self.session)
        self.topgg_webhook: WebhookManager = WebhookManager(self).dbl_webhook("/dbl", self.api["TopGGWH"])
        self.gist: GistClient = GistClient(self.api["GitHub"], self.session)
        self.sr: SRClient = SRClient()
        self.dagpi: DagpiClient = DagpiClient(self.api["DagpiAPI"], session=self.session)
        self.myst: mystbin.Client = mystbin.Client(session=self.session)
        self.loop.create_task(self.cache.populate_cache())
        self.loop.create_task(self.load_extensions())
        self.loop.create_task(self.start_nodes())
        self.loop.create_task(self.find_restart_message())
        self.topgg_webhook.run(8025)

    async def get_prefix(self, message: discord.Message) -> list[str]:
        prefixes: list[str] = [f"<@{self.user.id}>", f"<@!{self.user.id}>"]
        commands: tuple[str, ...] = ("dev", "developer", "jsk", "jishaku")
        if await self.is_owner(message.author) and message.content.lower().startswith(commands):
            prefixes.append("")
        if message.guild is None:
            prefixes.extend(DEFAULT_PREFIXES)
            return prefixes
        get_prefix = await self.cache.get_prefix(message.guild.id)

        if self.user.id == BETA_BOT_ID:
            prefixes.extend(BETA_PREFIXES)
        elif not get_prefix:
            prefixes.extend(DEFAULT_PREFIXES)
        else:
            prefixes.extend(get_prefix)
        command_prefix = "|".join(map(re.escape, prefixes))
        prefix: re.Match[str] | None = re.match(rf"^({command_prefix}\s*).*", message.content, flags=re.IGNORECASE)
        if prefix:
            prefixes.append(prefix[1])
        return prefixes

    async def load_extensions(self) -> None:
        for ext in self.to_load:
            try:
                await self.load_extension(ext)
            except commands.ExtensionError as error:
                _log.error("Exception in loading extension {ext}", exc_info=error)

    async def find_restart_message(self) -> None:
        await self.wait_until_ready()
        with open("reboot.toml", "r+") as f:
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
        try:
            node = await wavelink.NodePool.create_node(
                bot=self,
                host="127.0.0.1",
                port=2333,
                password="youshallnotpass",
                identifier="Avimetry",
                spotify_client=spotify.SpotifyClient(
                    client_id=self.api["SpotifyClientID"],
                    client_secret=self.api["SpotifySecret"],
                ),
            )
            _log.info(f"Wavelink node started: Identifier: {node.identifier}")
        except Exception as e:
            cog: ErrorHandler | None = self.get_cog("errorhandler")  # type: ignore
            if cog:
                await cog.error_webhook.send(str(e))
            await self.unload_extension("extensions.cogs.music")
            _log.error("Exception in starting Wavelink node", exc_info=e)

    async def on_ready(self) -> None:
        _log.info(f"Running: {self.user.name} ({self.user.id})")

    async def wait_for(
        self,
        event: str,
        *,
        check: Callable[..., bool] | None = None,
        timeout: float | None = None,
    ) -> Any:
        if event == "message":

            def bl_message_check(*args: Any) -> bool:
                if check:
                    return args[0].author.id not in self.cache.blacklist and check(*args)
                else:
                    return args[0].author.id not in self.cache.blacklist

            return await super().wait_for(event, check=bl_message_check, timeout=timeout)

        elif event in ("reaction_add", "reaction_remove"):

            def bl_reaction_check(*args) -> bool:
                if check:
                    return args[1].id not in self.cache.blacklist and check(*args)
                return args[1].id not in self.cache.blacklist

            return await super().wait_for(event, check=bl_reaction_check, timeout=timeout)
        else:
            bl_check = check
        return await super().wait_for(event, check=bl_check, timeout=timeout)

    async def wait_for_message(self, *, check=None, timeout=None) -> Any:
        return await self.wait_for("message", check=check, timeout=timeout)

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
            await self.command_cache[message.id].delete()
            self.command_cache.pop(message.id, None)

    async def is_owner(self, user: discord.User | discord.Member, /) -> bool:
        if user is not None:
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
        token = self.settings["bot_tokens"]["Avimetry"]
        super().run(token, reconnect=True, *args, **kwargs)

    async def close(self) -> None:
        await self.session.close()
        await self.sr.close()
        _log.info(f"Stopped: {self.user.name} ({self.user.id})")
        await super().close()
