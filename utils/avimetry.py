import discord
import os
import datetime
import sr_api
import aiohttp
import aiozaneapi
import mystbin
import topgg
import time
import re
import contextlib
import asyncpg
import asyncdagpi

from sys import platform
from discord.ext import commands
from config import tokens, postgresql
from .context import AvimetryContext
from .errors import Blacklisted
from .cache import AvimetryCache


os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"


DEFAULT_PREFIXES = ["A.", "a."]
BETA_PREFIXES = ["ab.", "ba."]
OWNER_IDS = {750135653638865017, 547280209284562944}
PUBLIC_BOT_ID = 756257170521063444
BETA_BOT_ID = 787046145884291072


async def bot_prefix(avi: "AvimetryBot", message: discord.Message):
    prefix_list = [f"<@{avi.user.id}>", f"<@!{avi.user.id}>"]
    if avi.user.id == BETA_BOT_ID:
        prefix_list.extend(BETA_PREFIXES)
    elif not message.guild or (get_prefix := await avi.cache.get_guild_settings(message.guild.id)) is None:
        prefix_list.extend(DEFAULT_PREFIXES)
    else:
        prefix_list.extend(get_prefix["prefixes"])
        if not prefix_list:
            prefix_list.extend(DEFAULT_PREFIXES)
    if await avi.is_owner(message.author):
        if message.content.lower().startswith(("dev", "jsk")):
            prefix_list.append("")
    command_prefix = "|".join(map(re.escape, prefix_list))
    prefix = re.match(rf"^({command_prefix}\s*).*", message.content, flags=re.IGNORECASE)
    if prefix:
        return prefix.group(1)
    print(prefix_list)
    return prefix_list


allowed_mentions = discord.AllowedMentions(
    everyone=False, users=False,
    roles=True, replied_user=False
)
intents = discord.Intents.default()
intents.members = True
activity = discord.Game("@Avimetry | 0 Servers")


class AvimetryBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            **kwargs,
            command_prefix=bot_prefix,
            case_insensitive=True,
            allowed_mentions=allowed_mentions,
            activity=activity,
            intents=intents,
            strip_after_prefix=True
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

        self.topgg = topgg.DBLClient(self, tokens["TopGG"], autopost_interval=None)
        self.sr = sr_api.Client()
        self.zaneapi = aiozaneapi.Client(tokens["ZaneAPI"])
        self.dagpi = asyncdagpi.Client(tokens["DagpiAPI"])
        self.myst = mystbin.Client()
        self.session = aiohttp.ClientSession()

        self.pool = self.loop.run_until_complete(asyncpg.create_pool(**postgresql))

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
                except commands.ExtensionAlreadyLoaded:
                    pass

    async def get_context(self, message, *, cls=AvimetryContext):
        return await super().get_context(message, cls=cls)

    async def process_commands(self, message):
        ctx = await self.get_context(message)
        if message.author == self.user:
            return
        if message.author.bot:
            return
        await self.invoke(ctx)

    async def on_message(self, message):
        await self.process_commands(message)

    async def postgresql_latency(self):
        start = time.perf_counter()
        await self.pool.execute("SELECT 1")
        end = time.perf_counter()
        return round((end - start) * 1000)

    async def api_latency(self, ctx):
        start = time.perf_counter()
        await ctx.trigger_typing()
        end = time.perf_counter()
        return round((end - start) * 1000)

    def run(self):
        if platform not in ["linux", "linux2"]:
            self.devmode = True
            token = tokens["AvimetryBeta"]
        else:
            token = tokens["Avimetry"]
        self.loop.run_until_complete(self.cache.cache_all())
        self.launch_time = datetime.datetime.utcnow()
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

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        if after.attachments:
            return
        await self.process_commands(after)
