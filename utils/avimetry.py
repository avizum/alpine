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

from sys import platform
from discord.ext import commands
from .context import AvimetryContext
from .errors import Blacklisted
from .cache import AvimetryCache
from .utils import Timer


os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


DEFAULT_PREFIXES = ["a."]
BETA_PREFIXES = ["ab.", "ba."]
OWNER_IDS = {750135653638865017, 547280209284562944}
PUBLIC_BOT_ID = 756257170521063444
BETA_BOT_ID = 787046145884291072


async def get_prefix(avi: "AvimetryBot", message: discord.Message):
    prefixes = [f"<@{avi.user.id}>", f"<@!{avi.user.id}>"]
    if not message.guild:
        prefixes.extend(DEFAULT_PREFIXES)
        return prefixes
    get_prefix = await avi.cache.get_guild_settings(message.guild.id)
    if avi.user.id == BETA_BOT_ID:
        prefixes.extend(BETA_PREFIXES)
    elif get_prefix is None:
        prefixes.extend(DEFAULT_PREFIXES)
    else:
        command_prefix = get_prefix["prefixes"]
        if not command_prefix:
            prefixes.extend(DEFAULT_PREFIXES)
        else:
            prefixes.extend(command_prefix)
    if await avi.is_owner(message.author) and message.content.startswith(
        ("jsk", "dev")
    ):
        prefixes.append("")
    command_prefix = "|".join(map(re.escape, prefixes))
    prefix = re.match(rf"^({command_prefix}\s*).*", message.content, flags=re.IGNORECASE)
    if prefix:
        prefixes.append(prefix.group(1))
    return prefixes


allowed_mentions = discord.AllowedMentions(
    everyone=False, users=False,
    roles=True, replied_user=False
)
intents = discord.Intents.all()
activity = discord.Game("Loading...")


class AvimetryBot(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            command_prefix=get_prefix,
            case_insensitive=True,
            allowed_mentions=allowed_mentions,
            activity=activity,
            intents=intents,
            strip_after_prefix=True,
            chunk_guilds_at_startup=False
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.owner_ids = OWNER_IDS
        self.bot_id = PUBLIC_BOT_ID
        self.launch_time = datetime.datetime.utcnow()
        self.commands_ran = 0
        self.command_cache = {}
        self.devmode = False
        self.cache = AvimetryCache(self)
        self.invite = str(discord.utils.oauth_url(PUBLIC_BOT_ID, discord.Permissions(2147483647)))
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
            "cogs.botinfo",
            "cogs.developer",
            "cogs.errorhandler",
            "cogs.events",
            "cogs.fun",
            "cogs.help",
            "cogs.highlight",
            "cogs.images",
            "cogs.jishaku",
            "cogs.joinsandleaves",
            "cogs.meta",
            "cogs.moderation",
            "cogs.myservers",
            "cogs.roblox",
            "cogs.servermanagement",
            "cogs.settings",
            "cogs.setup",
            "cogs.topgg",
            "cogs.verification"
        ]
        with open("config.toml") as f:
            self.settings = toml.loads(f.read())

        api = self.settings["api_tokens"]
        self.topgg = topgg.DBLClient(self, api["TopGG"], autopost_interval=None)
        self.sr = sr_api.Client()
        self.zaneapi = aiozaneapi.Client(api["ZaneAPI"])
        self.dagpi = asyncdagpi.Client(api["DagpiAPI"])
        self.myst = mystbin.Client()
        self.session = aiohttp.ClientSession()
        self.pool = self.loop.run_until_complete(asyncpg.create_pool(**self.settings["postgresql"]))
        self.loop.create_task(self.cache.cache_all())
        self.loop.create_task(self.chunk_guilds())

        @self.check
        async def check(ctx):
            if not ctx.guild:
                raise commands.NoPrivateMessage()
            if ctx.author.id in self.cache.blacklist:
                raise Blacklisted(reason=self.cache.blacklist[ctx.author.id])
            return True

        @self.event
        async def on_ready():
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
                except commands.ExtensionError as error:
                    print(error)

    async def get_context(self, message, *, cls=AvimetryContext):
        return await super().get_context(message, cls=cls)

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

    async def chunk_guilds(self):
        for guild in self.guilds:
            if not guild.chunked:
                await guild.chunk()

    async def postgresql_latency(self):
        with Timer() as e:
            await self.pool.execute("SELECT 1")
        return round(e.total_time * 1000)

    async def api_latency(self, ctx):
        with Timer() as e:
            await ctx.trigger_typing()
        return round((e.total_time) * 1000)

    def run(self):
        tokens = self.settings["bot_tokens"]
        if platform not in ["linux", "linux2"]:
            self.devmode = True
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
