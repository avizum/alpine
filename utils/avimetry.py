"""
The bot itself
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
import os
import datetime
import sr_api
import aiohttp
import aiozaneapi
import mystbin
import topgg
import toml
import re
import contextlib
import asyncpg
import asyncdagpi
import logging
import obsidian

from sys import platform
from discord.ext import commands
from .errors import Blacklisted, Maintenance
from .cache import AvimetryCache


os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


DEFAULT_PREFIXES = ["a."]
BETA_PREFIXES = ["ab.", "ba."]
OWNER_IDS = {750135653638865017, 547280209284562944}
PUBLIC_BOT_ID = 756257170521063444
BETA_BOT_ID = 787046145884291072


logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


async def get_prefix(avi: "AvimetryBot", message: discord.Message):
    prefixes = [f"<@{avi.user.id}>", f"<@!{avi.user.id}>"]
    if not message.guild:
        prefixes.extend(DEFAULT_PREFIXES)
        return prefixes
    get_prefix = await avi.cache.get_prefix(message.guild.id)

    if avi.user.id == BETA_BOT_ID:
        prefixes.extend(BETA_PREFIXES)
    elif not get_prefix:
        prefixes.extend(DEFAULT_PREFIXES)
    else:
        prefixes.extend(get_prefix)
    if await avi.is_owner(message.author) and message.content.startswith(("jsk", "dev")):
        prefixes.append("")
    command_prefix = "|".join(map(re.escape, prefixes))
    prefix = re.match(rf"^({command_prefix}\s*).*", message.content, flags=re.IGNORECASE)
    if prefix:
        prefixes.append(prefix.group(1))
    return prefixes


allowed_mentions = discord.AllowedMentions(
    everyone=False, users=False,
    roles=False, replied_user=False)

intents = discord.Intents(
    bans=True,
    emojis=True,
    guilds=True,
    messages=True,
    members=True,
    reactions=True,
    webhooks=True,
    voice_states=True)

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
            strip_after_prefix=True,
            chunk_guilds_at_startup=True
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.owner_ids = OWNER_IDS
        self.bot_id = PUBLIC_BOT_ID
        self.launch_time = datetime.datetime.utcnow()
        self.maintenance = False
        self.commands_ran = 0
        self.command_usage = {}
        self.command_cache = {}
        self.cache = AvimetryCache(self)
        self.invite = str(discord.utils.oauth_url(PUBLIC_BOT_ID, discord.Permissions(8)))
        self.emoji_dictionary = {
            "red_tick": '<:redtick:777096756865269760>',
            "green_tick": '<:greentick:777096731438874634>',
            "gray_tick": '<:graytick:791040199798030336>',
            "status_online": '<:status_online:810683593193029642>',
            "status_idle": '<:status_idle:810683571269664798>',
            "status_dnd": '<:status_dnd:810683560863989805>',
            "status_offline": '<:status_offline:810683581541515335',
            "status_streaming": '<:status_streaming:810683604812169276>'
        }
        self.bot_cogs = [
            "cogs.animals",
            "cogs.botinfo",
            "cogs.developer",
            "cogs.errorhandler",
            "cogs.events",
            "cogs.fun",
            "cogs.help",
            # "cogs.highlight",
            "cogs.images",
            "cogs.jishaku",
            "cogs.joinsandleaves",
            "cogs.meta",
            "cogs.moderation",
            "cogs.roblox",
            "cogs.servermanagement",
            "cogs.settings",
            # "cogs.music",
            "cogs.setup",
            "cogs.supportserver",
            "cogs.topgg",
            "cogs.verification",
            "utils.context"
        ]
        with open("config.toml") as token:
            self.settings = toml.loads(token.read())
        with open("pg_config.toml") as pg:
            self.pg = toml.loads(pg.read())

        api = self.settings["api_tokens"]
        self.topgg = topgg.DBLClient(self, api["TopGG"], autopost_interval=None)
        self.sr = sr_api.Client()
        self.zaneapi = aiozaneapi.Client(api["ZaneAPI"])
        self.dagpi = asyncdagpi.Client(api["DagpiAPI"])
        self.myst = mystbin.Client()
        self.session = aiohttp.ClientSession()
        self.pool = self.loop.run_until_complete(asyncpg.create_pool(**self.pg["postgresql"]))
        self.loop.create_task(self.cache.cache_all())
        # self.loop.create_task(self.initiate_obsidian())

        @self.check
        async def check(ctx):
            if not ctx.guild:
                raise commands.NoPrivateMessage()
            if ctx.author.id in self.cache.blacklist:
                raise Blacklisted(reason=self.cache.blacklist[ctx.author.id])
            if ctx.bot.maintenance is True:
                raise Maintenance()
            return True

    async def initiate_obsidian(self):
        self.obsidian = await obsidian.initiate_node(self)

    async def on_ready(self):
        await self.wait_until_ready()
        timenow = datetime.datetime.now().strftime("%I:%M %p")
        print(
            "Successfully logged in:\n"
            f"Username: {self.user.name}\n"
            f"Bot ID: {self.user.id}\n"
            f"Login Time: {datetime.date.today()} at {timenow}\n"
        )
        for cog in self.bot_cogs:
            try:
                self.load_extension(cog)
            except commands.ExtensionAlreadyLoaded:
                pass
            except commands.ExtensionError as error:
                print(error)

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

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or self.context)

    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message)
        if message.author == self.user:
            return
        if message.author.bot:
            return
        await self.invoke(ctx)

    async def on_message(self, message):
        await self.process_commands(message)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        if after.attachments:
            return
        await self.process_commands(after)

    async def on_message_delete(self, message: discord.Message):
        if message.id in self.command_cache:
            try:
                await self.command_cache[message.id].delete()
                self.command_cache.pop(message.id)
            except Exception:
                pass

    def run(self):
        tokens = self.settings["bot_tokens"]
        if platform not in ["linux", "linux2"]:
            token = tokens["AvimetryBeta"]
        else:
            token = tokens["Avimetry"]
        super().run(token, reconnect=True)

    async def close(self):
        with contextlib.suppress(Exception):
            await self.sr.close()
            await self.zaneapi.close()
            await self.myst.close()
            await self.session.close()
            await self.dagpi.close()
            await self.topgg.close()
            await super().close()
        print("\nSuccessfully closed bot", end="\n\n")
