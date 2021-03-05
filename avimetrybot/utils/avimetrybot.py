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
from utils import AvimetryContext
from .errors import Blacklisted
from discord.ext import commands
from utils.mongo import MongoDB
from akinator.async_aki import Akinator
from config import tokens

DEFAULT_PREFIXES = ['A.', 'a.']
OWNER_IDS = {750135653638865017, 547280209284562944}
PUBLIC_BOT_ID = 756257170521063444
BETA_BOT_ID = 787046145884291072


async def prefix(avimetry, message):
    if avimetry.devmode is True:
        command_prefix = ""
    get_prefix = await avimetry.config.find(message.guild.id)
    if not message.guild or "prefix" not in get_prefix:
        command_prefix = DEFAULT_PREFIXES
    else:
        command_prefix = get_prefix["prefix"]
        if command_prefix is None:
            command_prefix = DEFAULT_PREFIXES
    command_prefix = re.escape(command_prefix)
    match = re.match(rf"^({command_prefix}\s*).*", message.content, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return commands.when_mentioned(avimetry, message)

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
            command_prefix=prefix,
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
        self.emoji_dictionary = {
            "NoTick": '<:noTick:777096756865269760>',
            "YesTick": '<:yesTick:777096731438874634>',
            "StatusOnline": '<:status_online:810683593193029642>',
            "StatusIdle": '<:status_idle:810683571269664798>',
            "StatusDND": '<:status_dnd:810683560863989805>',
            "StatusOffline": '<:status_offline:810683581541515335',
            "StatusStreaming": '<:status_streaming:810683604812169276>'
        }

        # API Variables
        self.sr = sr_api.Client()
        self.zaneapi = aiozaneapi.Client(tokens["ZaneAPI"])
        self.myst = mystbin.Client()
        self.session = aiohttp.ClientSession()
        self.akinator = Akinator()

        # Database
        self.mongo = motor.motor_asyncio.AsyncIOMotorClient(tokens["MongoDB"])
        self.db = self.mongo["avimetry"]
        self.config = MongoDB(self.db, "new")
        self.mutes = MongoDB(self.db, "mutes")
        self.logs = MongoDB(self.db, "logging")
        self.bot_users = MongoDB(self.db, "users")
        self.blacklist = MongoDB(self.db, "blacklisted")

        @self.check
        async def globally_block_dms(ctx):
            if not ctx.guild:
                raise commands.NoPrivateMessage("Commands do not work in dm channels.")
            return True

        @self.check
        async def is_blacklisted(ctx):
            if ctx.author.id in self.blacklisted_users:
                raise Blacklisted()
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

            current_mutes = await self.mutes.get_all()
            for mute in current_mutes:
                self.muted_users[mute["_id"]] = mute

            current_blacklisted = await self.blacklist.get_all()
            for blacklist in current_blacklisted:
                self.blacklisted_users[blacklist["_id"]] = blacklist

        os.environ["JISHAKU_HIDE"] = "True"
        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
        os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
        for filename in os.listdir("./avimetrybot/cogs"):
            if filename.endswith(".py"):
                self.load_extension(f"cogs.{filename[:-3]}")

    async def get_context(self, message, *, cls=AvimetryContext):
        return await super().get_context(message, cls=cls)

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
        self.mongo.close()
        await self.sr.close()
        await self.zaneapi.close()
        await self.myst.close()
        await self.session.close()
        print("\nClosing Connection to Discord.")
        await super().close()

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.id in self.owner_ids:
            if before.content != after.content:
                await self.process_commands(after)
