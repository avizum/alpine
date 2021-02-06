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
import aiozaneapi
import sr_api
import aiohttp
import sys
import contextlib
from pathlib import Path
from utils.context import AvimetryContext

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

allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=True)
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
        self.zane=aiozaneapi.Client(os.getenv('Zane_Token'))
        self.sr=sr_api.Client()

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

class MongoDB:
    def __init__(self, connection, document_name):
        self.db = connection[document_name]
        self.logger = logging.getLogger(__name__)

    async def update(self, dict):
        await self.update_by_id(dict)

    async def get_by_id(self, id):
        return await self.find_by_id(id)

    async def find(self, id):
        return await self.find_by_id(id)

    async def delete(self, id):
        await self.delete_by_id(id)

    async def find_by_id(self, id):
        return await self.db.find_one({"_id": id})

    async def delete_by_id(self, id):
        if not await self.find_by_id(id):
            return

        await self.db.delete_many({"_id": id})

    async def insert(self, dict):
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected a dictionary.")
        if not dict["_id"]:
            raise KeyError("_id not couldn't be found in given dictionary.")
        await self.db.insert_one(dict)
    async def upsert(self, dict):
        if await self.__get_raw(dict["_id"]) != None:
            await self.update_by_id(dict)
        else:
            await self.db.insert_one(dict)

    async def update_by_id(self, dict):
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected a dictionary.")

        # Always use your own _id
        if not dict["_id"]:
            raise KeyError("_id not couldn't be found in given dictionary.")

        if not await self.find_by_id(dict["_id"]):
            return

        id = dict["_id"]
        dict.pop("_id")
        await self.db.update_one({"_id": id}, {"$set": dict})

    async def unset(self, dict):
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected a dictionary.")
        if not dict["_id"]:
            raise KeyError("_id not couldn't be found in given dictionary.")

        if not await self.find_by_id(dict["_id"]):
            return

        id = dict["_id"]
        dict.pop("_id")
        await self.db.update_one({"_id": id}, {"$unset": dict})

    async def increment(self, id, amount, field):
        if not await self.find_by_id(id):
            return

        await self.db.update_one({"_id": id}, {"$inc": {field: amount}})

    async def get_all(self):
        data = []
        async for document in self.db.find({}):
            data.append(document)
        return data

    async def __get_raw(self, id):
        return await self.db.find_one({"_id": id})
