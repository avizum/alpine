from important import AvimetryContext
import discord
import os
import datetime
import pymongo
from pymongo import MongoClient
from discord.ext import commands, tasks
from dotenv import load_dotenv
import collections
import logging
import motor.motor_asyncio
import pathlib
import sr_api
import aiohttp
import sys
import contextlib
import aiozaneapi
from pathlib import Path
from important.mongo import MongoDB
import mystbin


class Silence:
    def write(self, msg):
        pass

async def prefix(avimetrybot, message):
    if not message.guild:
        return "a."
    try:
        data=await avimetrybot.config.find(message.guild.id)
        if not data or "prefix" not in data:
            await avimetrybot.config.upsert({"_id": message.guild.id, "prefix": "a."})
            await message.channel.send("No prefix found for this server, so I set it as **a.**")
        return data["prefix"]
    except:
        return "a."

allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=False)
intents=discord.Intents.all()
activity=discord.Game('avimetry() | a.help')

class AvimetryBot(commands.Bot):
    def __init__(self):
        intents=discord.Intents.all()
        super().__init__(
            command_prefix=prefix,
            case_insensitive=True,
            allowed_mentions=allowed_mentions,
            activity=activity,
            intents=intents
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()

        self.launch_time=datetime.datetime.utcnow()
        self.muted_users={}
        self.devmode=False
        self.zanetoken=(os.getenv("Zane_Token"))
        self.sr=sr_api.Client()
        self.zaneapi=aiozaneapi.Client(os.getenv("Zane_Token"))
        self.myst=mystbin.Client()


        @self.check
        async def globally_block_dms(ctx):
            if not ctx.guild:
                raise commands.NoPrivateMessage("Commands do not work in dm channels.")
            return True

        @tasks.loop(seconds=1)
        async def load_important():
            important=('jishaku', 'owner')
            for load in important:
                cog="cogs." if load !="jishaku" else ""
                try:
                    self.load_extension(f"{cog}{important}")
                except:
                    pass
        
        @self.event
        async def on_ready():
            load_important.start()
            self.mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('DB_Token'))
            self.db=self.mongo['avimetry']
            self.config=MongoDB(self.db, 'new')
            self.mutes=MongoDB(self.db, 'mutes')
            self.logs=MongoDB(self.db, 'logging')
            
            current_mutes=await self.mutes.get_all()
            for mute in current_mutes:
                self.muted_users[mute["_id"]] = mute
        
        os.environ["JISHAKU_HIDE"] = "True"
        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
        os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 
        self.load_extension('jishaku')
        for filename in os.listdir('./avimetrybot/cogs'):
            if filename.endswith('.py'):
                self.load_extension(f'cogs.{filename[:-3]}')

    async def get_context(self, message, *, cls=AvimetryContext):
        return await super().get_context(message, cls=cls)

    async def close(self):
        with contextlib.suppress(Exception):
            sys.stderr=Silence()
            await super().close()
        
        
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.id in self.owner_ids:
            await self.process_commands(after)