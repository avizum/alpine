import discord
import os
import datetime
import motor.motor_asyncio
import sr_api
import aiohttp
import aiozaneapi
import mystbin
import time
import re
import asyncpg
from utils import AvimetryContext
from .errors import Blacklisted
from discord.ext import commands
from utils.mongo import MongoDB
from config import tokens, postgresql
from copy import deepcopy


DEFAULT_PREFIXES = ["A.", "a."]
BETA_PREFIXES = ["ab.", "ba."]
OWNER_IDS = {750135653638865017, 547280209284562944}
PUBLIC_BOT_ID = 756257170521063444
BETA_BOT_ID = 787046145884291072


async def escape_prefix(prefixes):
    if isinstance(prefixes, str):
        return re.escape(prefixes)
    if isinstance(prefixes, list):
        return '|'.join(map(re.escape, prefixes))


async def bot_prefix(avi, message: discord.Message):
    if avi.user.id == BETA_BOT_ID:
        command_prefix = BETA_PREFIXES
    if not message.guild or (get_prefix := await avi.temp.get_guild_settings(message.guild.id)) is None:
        command_prefix = DEFAULT_PREFIXES
    else:
        command_prefix = get_prefix["prefixes"]
        if not command_prefix:
            return DEFAULT_PREFIXES
    command_prefix = await escape_prefix(command_prefix)
    prefix = re.match(rf"^({command_prefix}\s*).*", message.content, flags=re.IGNORECASE)
    if prefix:
        return prefix.group(1)
    return commands.when_mentioned(avi, message)

allowed_mentions = discord.AllowedMentions(
    everyone=False, users=False,
    roles=True, replied_user=False
)
intents = discord.Intents.all()
activity = discord.Game("Avimetry | @Avimetry help")


class AvimetryBot(commands.Bot):
    def __init__(self, **kwargs):
        intents = discord.Intents.all()
        super().__init__(
            **kwargs,
            command_prefix=bot_prefix,
            case_insensitive=True,
            allowed_mentions=allowed_mentions,
            activity=activity,
            intents=intents,
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.owner_ids = OWNER_IDS
        self.bot_id = PUBLIC_BOT_ID

        # Bot Variables
        self.launch_time = datetime.datetime.utcnow()
        self.muted_users = {}
        self.blacklisted_users = {}
        self.commands_ran = 0
        self.devmode = False
        self.temp = AvimetryCache(self)
        self.emoji_dictionary = {
            "red_tick": '<:noTick:777096756865269760>',
            "green_tick": '<:yesTick:777096731438874634>',
            "status_online": '<:status_online:810683593193029642>',
            "status_idle": '<:status_idle:810683571269664798>',
            "status_dnd": '<:status_dnd:810683560863989805>',
            "status_offline": '<:status_offline:810683581541515335',
            "status_streaming": '<:status_streaming:810683604812169276>'
        }

        # API Variables
        self.sr = sr_api.Client()
        self.zaneapi = aiozaneapi.Client(tokens["ZaneAPI"])
        self.myst = mystbin.Client()
        self.session = aiohttp.ClientSession()

        # Database
        self.pool = self.loop.run_until_complete(asyncpg.create_pool(**postgresql))
        # TODO: Migrate all data to postgres.
        self.mongo = motor.motor_asyncio.AsyncIOMotorClient(tokens["MongoDB"])
        self.db = self.mongo["avimetry"]
        self.config = MongoDB(self.db, "new")
        self.mutes = MongoDB(self.db, "mutes")
        self.logs = MongoDB(self.db, "logging")
        self.bot_users = MongoDB(self.db, "users")
        self.blacklist = MongoDB(self.db, "blacklisted")

        @self.check
        async def check(ctx):
            if not ctx.guild:
                raise commands.NoPrivateMessage()
            if ctx.author.id in self.temp.blacklisted_users:
                raise Blacklisted(reason=self.temp.blacklisted_users[ctx.author.id])
            return True

        @self.event
        async def on_ready():
            timenow = datetime.datetime.now().strftime("%I:%M %p")
            print(
                "------\n"
                "Succesfully logged in. Bot Info Below:\n"
                f"Username: {self.user.name}\n"
                f"Bot ID: {self.user.id}\n"
                f"Login Time: {datetime.date.today()} at {timenow}\n"
                "------"
            )

        os.environ["JISHAKU_HIDE"] = "True"
        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
        os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
        for filename in os.listdir("./avimetrybot/cogs"):
            if filename.endswith(".py"):
                self.load_extension(f"cogs.{filename[:-3]}")

    async def get_context(self, message, *, cls=AvimetryContext):
        return await super().get_context(message, cls=cls)

    async def postgresql_latency(self):
        start = time.perf_counter()
        await self.pool.execute("SELECT 1")
        end = time.perf_counter()
        return round((end-start) * 1000)

    async def api_latency(self, ctx):
        start = time.perf_counter()
        await ctx.trigger_typing()
        end = time.perf_counter()
        return round((end - start) * 1000)

    async def database_latency(self, ctx):
        start = time.perf_counter()
        await self.config.find({"_id": ctx.guild.id})
        end = time.perf_counter()
        return round((end - start) * 1000)

    async def close(self):
        await self.change_presence(status=discord.Status.offline)
        self.mongo.close()
        await self.sr.close()
        await self.zaneapi.close()
        await self.myst.close()
        await self.session.close()
        print("\nClosing Connection to Discord.")
        await super().close()

    def run(self, *args, **kwargs):
        self.loop.run_until_complete(self.temp.cache_all())
        super().run(*args, **kwargs)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.process_commands(after)


class AvimetryCache:
    def __init__(self, avi: AvimetryBot):
        self.avi = avi
        self.guild_settings_cache = {}
        self.blacklisted_users = {}

    async def cache_all(self):
        await self.load_guild_settings()
        await self.load_blacklisted()

    async def get_guild_settings(self, guild_id: int):
        return self.guild_settings_cache.get(guild_id, None)

    async def cache_new_guild(self, guild_id: int):
        await self.avi.pool.execute("INSERT INTO guild_settings VALUES ($1)", guild_id)
        self.guild_settings_cache[guild_id] = deepcopy({"prefixes": []})
        return self.guild_settings_cache[guild_id]

    async def load_guild_settings(self):
        items = await self.avi.pool.fetch("SELECT * FROM guild_settings")
        for entry in items:
            self.guild_settings_cache[entry["guild_id"]] = {key: value for key, value in list(entry.items())}

    async def load_blacklisted(self):
        items = await self.avi.pool.fetch("SELECT * FROM blacklist_user")
        for entry in items:
            self.blacklisted_users[entry["user_id"]] = entry["bl_reason"]
