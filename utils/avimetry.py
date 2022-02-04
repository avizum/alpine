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

import datetime
import logging
import os
import re

import aiohttp
import asyncdagpi
import asyncpg
import core
import discord
import mystbin
import sr_api
import toml
import topgg
import wavelink
from asyncgist import Client
from discord.ext import commands
from wavelink.ext import spotify

from core import Command, Group
from .cache import AvimetryCache
from .exceptions import (
    Blacklisted,
    CommandDisabledChannel,
    CommandDisabledGuild,
    Maintenance
)

os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


DEFAULT_PREFIXES = ["a."]
BETA_PREFIXES = ["ab.", "ba."]
OWNER_IDS = {
    750135653638865017,
    547280209284562944,
    765098549099626507,
    756757268736901120,
}
PUBLIC_BOT_ID = 756257170521063444
BETA_BOT_ID = 787046145884291072


logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


async def get_prefix(bot: "AvimetryBot", message: discord.Message):
    prefixes = [f"<@{bot.user.id}>", f"<@!{bot.user.id}>"]
    commands = ("dev", "developer", "jsk", "jishaku")
    if (
        await bot.is_owner(message.author)
        and message.content.lower().startswith(commands)
        and message.guild
    ):
        prefixes.append("")
    elif not message.guild:
        prefixes.extend(DEFAULT_PREFIXES)
        return prefixes
    get_prefix = await bot.cache.get_prefix(message.guild.id)

    if bot.user.id == BETA_BOT_ID:
        prefixes.extend(BETA_PREFIXES)
    elif not get_prefix:
        prefixes.extend(DEFAULT_PREFIXES)
    else:
        prefixes.extend(get_prefix)
    command_prefix = "|".join(map(re.escape, prefixes))
    prefix = re.match(
        rf"^({command_prefix}\s*).*", message.content, flags=re.IGNORECASE
    )
    if prefix:
        prefixes.append(prefix.group(1))
    return prefixes


allowed_mentions = discord.AllowedMentions.none()

intents = discord.Intents(
    bans=True,
    emojis=True,
    guilds=True,
    messages=True,
    members=True,
    reactions=True,
    webhooks=True,
    voice_states=True,
)

activity = discord.Game("Loading...")


class AvimetryBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            command_prefix=get_prefix,
            case_insensitive=True,
            allowed_mentions=allowed_mentions,
            activity=activity,
            intents=intents,
            status=discord.Status.idle,
            chunk_guilds_at_startup=True,
            max_messages=5000,
            slash_commands=False,
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.owner_ids = OWNER_IDS
        self.bot_id = PUBLIC_BOT_ID
        self.core = core
        self.launch_time = datetime.datetime.now(datetime.timezone.utc)
        self.maintenance = False
        self.commands_ran = 0
        self.command_usage = {}
        self.command_cache = {}
        self.cache = AvimetryCache(self)
        self.invite = str(
            discord.utils.oauth_url(PUBLIC_BOT_ID, permissions=discord.Permissions(8))
        )
        self.support = "https://discord.gg/muTVFgDvKf"
        self.source = "https://github.com/avimetry/avimetry"
        self.emoji_dictionary = {
            "red_tick": "<:redtick:777096756865269760>",
            "green_tick": "<:greentick:777096731438874634>",
            "gray_tick": "<:graytick:791040199798030336>",
            "status_online": "<:status_online:810683593193029642>",
            "status_idle": "<:status_idle:810683571269664798>",
            "status_dnd": "<:status_dnd:810683560863989805>",
            "status_offline": "<:status_offline:810683581541515335",
            "status_streaming": "<:status_streaming:810683604812169276>",
        }
        self.primary_extensions = [
            "extensions.listeners.events",
            "extensions.cogs.owner",
            "extensions.extras.setup",
            "utils.context",
        ]
        self.secondary_extensions = [
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
            self.settings = toml.loads(token.read())
        api = self.settings["api_tokens"]
        self.news = self.settings["news"]["news"]
        self.session = aiohttp.ClientSession()
        self.topgg = topgg.DBLClient(
            self, api["TopGG"], autopost_interval=None, session=self.session
        )
        self.gist = Client(api["GitHub"], self.session)
        self.sr = sr_api.Client()
        self.dagpi = asyncdagpi.Client(api["DagpiAPI"], session=self.session)
        self.myst = mystbin.Client(session=self.session)
        self.pool = self.loop.run_until_complete(
            asyncpg.create_pool(**self.settings["postgresql"])
        )
        self.loop.create_task(self.cache.populate_cache())
        self.loop.create_task(self.load_extensions())
        self.loop.create_task(self.start_nodes())
        self.loop.create_task(self.find_restart_message())

        @self.check
        async def check(ctx):
            if not ctx.guild and not await self.is_owner(ctx.author):
                raise commands.NoPrivateMessage()
            if ctx.author.id in self.cache.blacklist:
                raise Blacklisted(reason=self.cache.blacklist[ctx.author.id])
            if (
                str(ctx.command)
                in ctx.cache.guild_settings[ctx.guild.id]["disabled_commands"]
            ):
                raise CommandDisabledGuild()
            if (
                ctx.channel.id
                in ctx.cache.guild_settings[ctx.guild.id]["disabled_channels"]
            ):
                raise CommandDisabledChannel()
            if ctx.bot.maintenance is True:
                raise Maintenance()
            return True

    def __repr__(self):
        return f"<AvimetryBot id={self.user.id}>"

    async def load_extensions(self):
        for ext in self.primary_extensions:
            try:
                self.load_extension(ext)
            except commands.ExtensionError as error:
                print(error)
        await self.wait_until_ready()
        for ext in self.secondary_extensions:
            try:
                self.load_extension(ext)
            except commands.ExtensionError as error:
                print(error)

    async def find_restart_message(self):
        await self.wait_until_ready()
        with open("reboot.toml", "r+") as f:
            info = toml.loads(f.read())
            if info:
                channel = self.get_channel(info["channel_id"])
                message = channel.get_partial_message(info["message_id"])
                if message:
                    now = datetime.datetime.now(tz=datetime.timezone.utc)
                    await message.edit(
                        content=f"Took {(now - info['restart_time']).seconds} seconds to restart."
                    )
                f.truncate(0)
            f.close()

    async def start_nodes(self) -> None:
        await self.wait_until_ready()

        api_tokens = self.settings["api_tokens"]
        await wavelink.NodePool.create_node(
            bot=self,
            host="127.0.0.1",
            port=2333,
            password="youshallnotpass",
            identifier="MAIN",
            spotify_client=spotify.SpotifyClient(
                client_id=api_tokens["SpotifyClientID"],
                client_secret=api_tokens["SpotifySecret"]
            )
        )

    async def on_ready(self):
        timenow = datetime.datetime.now().strftime("%I:%M %p")
        print(
            "Successfully logged in:\n"
            f"Username: {self.user.name}\n"
            f"Bot ID: {self.user.id}\n"
            f"Login Time: {datetime.date.today()} at {timenow}\n"
        )

    async def wait_for(self, event, *, check=None, timeout=None):
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

    async def wait_for_message(self, *, check=None, timeout=None):
        return await self.wait_for("message", check=check, timeout=timeout)

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or self.context)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content or after.attachments:
            return
        await self.process_commands(after)

    async def on_message_delete(self, message: discord.Message):
        if message.id in self.command_cache:
            try:
                await self.command_cache[message.id].delete()
                self.command_cache.pop(message.id)
            except Exception:
                pass

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

    def run(self):
        tokens = self.settings["bot_tokens"]
        token = tokens["Avimetry"]
        super().run(token, reconnect=True)

    async def close(self):
        await self.session.close()
        await self.sr.close()
        await super().close()
        timenow = datetime.datetime.now(datetime.timezone.utc).strftime("%I:%M %p")
        print(
            f"\n{self.user.name} logged out:\n"
            f"Logged out time: {datetime.date.today()} at {timenow}",
            end="\n\n",
        )
