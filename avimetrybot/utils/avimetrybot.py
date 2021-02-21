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
from discord.ext import commands
from utils.mongo import MongoDB
from akinator.async_aki import Akinator

DEFAULT_PREFIXES = ['A.', 'a.']
OWNER_IDS = {750135653638865017, 547280209284562944}
BOT_ID = 756257170521063444


async def prefix(avimetry, message):
    get_prefix = await avimetry.config.find(message.guild.id)
    if not message.guild or "prefix" not in get_prefix:
        command_prefix = DEFAULT_PREFIXES
    else:
        command_prefix = get_prefix["prefix"]
        if command_prefix is None:
            command_prefix = DEFAULT_PREFIXES
    match = re.match(rf"^({command_prefix}\s*).*", message.content, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return commands.when_mentioned(avimetry, message)

allowed_mentions = discord.AllowedMentions(
    everyone=False, users=False,
    roles=True, replied_user=False
)
intents = discord.Intents.all()
activity = discord.Game("avimetry() | a.help")


class AvimetryBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="a.",
            case_insensitive=True,
            allowed_mentions=allowed_mentions,
            activity=activity,
            intents=intents,
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()

        self.launch_time = datetime.datetime.utcnow()
        self.muted_users = {}
        self.devmode = False
        self.zanetoken = os.getenv("Zane_Token")
        self.sr = sr_api.Client()
        self.zaneapi = aiozaneapi.Client(os.getenv("Zane_Token"))
        self.myst = mystbin.Client()
        self.commands_ran = 0
        self.session = aiohttp.ClientSession()
        self.akinator = Akinator()
        self.owner_ids = OWNER_IDS
        self.bot_id = BOT_ID

        @self.check
        async def globally_block_dms(ctx):
            if not ctx.guild:
                raise commands.NoPrivateMessage("Commands do not work in dm channels.")
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

            self.mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("DB_Token"))
            self.db = self.mongo["avimetry"]
            self.config = MongoDB(self.db, "new")
            self.mutes = MongoDB(self.db, "mutes")
            self.logs = MongoDB(self.db, "logging")
            self.bot_users = MongoDB(self.db, "users")
            current_mutes = await self.mutes.get_all()
            for mute in current_mutes:
                self.muted_users[mute["_id"]] = mute

        os.environ["JISHAKU_HIDE"] = "True"
        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
        os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
        # self.load_extension('jishaku')
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
            if before.content == after.content:
                await self.process_commands(after)
