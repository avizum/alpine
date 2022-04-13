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

import asyncdagpi
import asyncpg
import asyncgist
import discord
import jishaku
import mystbin
import sr_api
import toml
import wavelink
from aiohttp import ClientSession

from discord.ext import commands
from wavelink.ext import spotify
from topgg import DBLClient
from topgg.webhook import WebhookManager

from core import Command, Group
from utils.cache import Cache
from .exceptions import Blacklisted, CommandDisabledChannel, CommandDisabledGuild, Maintenance

if TYPE_CHECKING:
    from .context import Context


jishaku.Flags.HIDE = True
jishaku.Flags.NO_UNDERSCORE = True
jishaku.Flags.NO_DM_TRACEBACK = True


DEFAULT_PREFIXES: list[str] = ["a.", "avimetry"]
BETA_PREFIXES: list[str] = ["ab.", "ba."]
OWNER_IDS: set[str] = {
    750135653638865017,
    547280209284562944,
    765098549099626507,
    756757268736901120,
}
PUBLIC_BOT_ID: int = 756257170521063444
BETA_BOT_ID: int = 787046145884291072


logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


class Bot(commands.Bot):
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

    emoji_dictionary: dict[str, str] = {
        "red_tick": "<:redtick:777096756865269760>",
        "green_tick": "<:greentick:777096731438874634>",
        "gray_tick": "<:graytick:791040199798030336>",
        "status_online": "<:status_online:810683593193029642>",
        "status_idle": "<:status_idle:810683571269664798>",
        "status_dnd": "<:status_dnd:810683560863989805>",
        "status_offline": "<:status_offline:810683581541515335",
        "status_streaming": "<:status_streaming:810683604812169276>",
    }

    primary_extensions: list[str] = [
        "extensions.listeners.events",
        "extensions.cogs.owner",
        "extensions.extras.setup",
        "core.context",
    ]

    secondary_extensions: list[str] = [
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
    ]

    with open("config.toml") as token:
        settings: dict[str, Any] = toml.loads(token.read())
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
            slash_commands=False,
            owner_ids=OWNER_IDS,
        )
        self._BotBase__cogs: dict[str, commands.Cog] = commands.core._CaseInsensitiveDict()
        self.add_check(self.bot_check)

    def __repr__(self) -> str:
        return f"<Bot id={self.user.id}>"

    async def setup_hook(self) -> None:
        self.session: ClientSession = ClientSession()
        self.cache: Cache = Cache(self)
        self.pool: asyncpg.Pool = await asyncpg.create_pool(**self.settings["postgresql"])
        self.topgg: DBLClient = DBLClient(self, self.api["TopGG"], autopost_interval=None, session=self.session)
        self.topgg_webhook: WebhookManager = WebhookManager(self).dbl_webhook("/dbl", self.api["TopGGWH"])
        self.gist: asyncgist.Client = asyncgist.Client(self.api["GitHub"], self.session)
        self.sr: sr_api = sr_api.Client()
        self.dagpi: asyncgist.Client = asyncdagpi.Client(self.api["DagpiAPI"], session=self.session)
        self.myst: mystbin.Client = mystbin.Client(session=self.session)
        self.loop.create_task(self.cache.populate_cache())
        self.loop.create_task(self.load_extensions())
        self.loop.create_task(self.start_nodes())
        self.loop.create_task(self.find_restart_message())
        self.topgg_webhook.run(8025)

    async def get_prefix(self, message: discord.Message) -> list[str]:
        prefixes: list[str] = [f"<@{self.user.id}>", f"<@!{self.user.id}>"]
        commands: tuple[str] = ("dev", "developer", "jsk", "jishaku")
        if await self.is_owner(message.author) and message.content.lower().startswith(commands):
            prefixes.append("")
        elif not message.guild:
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
        prefix: re.Match = re.match(rf"^({command_prefix}\s*).*", message.content, flags=re.IGNORECASE)
        if prefix:
            prefixes.append(prefix.group(1))
        return prefixes

    async def bot_check(self, ctx: Context) -> bool:
        if ctx.author.id in self.cache.blacklist:
            raise Blacklisted(reason=self.cache.blacklist[ctx.author.id])
        if not ctx.guild:
            return True
        if str(ctx.command) in ctx.cache.guild_settings[ctx.guild.id]["disabled_commands"]:
            raise CommandDisabledGuild()
        if ctx.channel.id in ctx.cache.guild_settings[ctx.guild.id]["disabled_channels"]:
            raise CommandDisabledChannel()
        if ctx.bot.maintenance is True:
            raise Maintenance()
        return True

    async def load_extensions(self) -> None:
        for ext in self.primary_extensions:
            try:
                await self.load_extension(ext)
            except commands.ExtensionError as error:
                print(error)
        await self.wait_until_ready()
        for ext in self.secondary_extensions:
            try:
                await self.load_extension(ext)
            except commands.ExtensionError as error:
                print(error)

    async def find_restart_message(self) -> None:
        await self.wait_until_ready()
        with open("reboot.toml", "r+") as f:
            info = toml.loads(f.read())
            if info:
                channel: discord.abc.GuildChannel = self.get_channel(info["channel_id"])
                message: discord.PartialMessage = channel.get_partial_message(info["message_id"])
                if message:
                    now: datetime = datetime.now(tz=dt.timezone.utc)
                    await message.edit(content=f"Took {(now - info['restart_time']).seconds} seconds to restart.")
                f.truncate(0)
            f.close()

    async def start_nodes(self) -> None:
        await self.wait_until_ready()

        try:
            await wavelink.NodePool.create_node(
                bot=self,
                host="127.0.0.1",
                port=2333,
                password="youshallnotpass",
                identifier="MAIN",
                spotify_client=spotify.SpotifyClient(
                    client_id=self.api["SpotifyClientID"], client_secret=self.api["SpotifySecret"]
                ),
            )
        except Exception as e:
            cog: commands.Cog = self.get_cog("errorhandler")
            if cog:
                await cog.error_webhook.send(str(e))
            self.unload_extension("extensions.cogs.music")

    async def on_ready(self) -> None:
        timenow: str = datetime.now().strftime("%m/%d/%Y at %I:%M %p")
        print(
            "Successfully logged in:\n"
            f"Username: {self.user.name}\n"
            f"Bot ID: {self.user.id}\n"
            f"Login Time: {timenow}\n"
        )

    async def wait_for(
        self, event: str, *, check: Callable[..., bool] | None = None, timeout: float | None = None
    ) -> Any:
        if event == "message":

            def bl_check(*args):
                if not check:
                    return args[0].author.id not in self.cache.blacklist
                return args[0].author.id not in self.cache.blacklist and check(*args)

        elif event in ("reaction_add", "reaction_remove"):

            def bl_check(*args):
                if not check:
                    return args[1].id not in self.cache.blacklist
                return args[1].id not in self.cache.blacklist and check(*args)

        else:
            bl_check = check
        return await super().wait_for(event, check=bl_check, timeout=timeout)

    async def wait_for_message(self, *, check=None, timeout=None) -> Any:
        return await self.wait_for("message", check=check, timeout=timeout)

    async def get_context(self, message: discord.Message, *, cls=None) -> Context:
        return await super().get_context(message, cls=cls or self.context)

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.content == after.content or after.attachments:
            return
        await self.process_commands(after)

    async def on_message_delete(self, message: discord.Message) -> None:
        if message.id in self.command_cache:
            try:
                await self.command_cache[message.id].delete()
                self.command_cache.pop(message.id)
            except Exception:
                pass

    def command(self, name=None, cls=None, **kwargs) -> Command:
        if cls is None:
            cls = Command

        def decorator(func):
            if isinstance(func, Command):
                raise TypeError("Callback is already a command")
            res = cls(func, name=name, **kwargs)
            self.add_command(res)
            return res

        return decorator

    def group(self, name=None, **kwargs) -> Group:
        return self.command(name=name, cls=Group, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> None:
        tokens = self.settings["bot_tokens"]
        token = tokens["Avimetry"]
        super().run(token, reconnect=True, *args, **kwargs)

    async def close(self) -> None:
        await self.session.close()
        await self.sr.close()
        await super().close()
        timenow: str = datetime.now().strftime("%m/%d/%Y at %I:%M %p")
        print(
            f"\n{self.user.name} logged out:\n" f"Logged out time: {timenow}",
            end="\n\n",
        )
