from utils import AvimetryContext
import discord
import os
import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv
import logging
import motor.motor_asyncio
import pathlib
import sr_api
import aiohttp
import aiozaneapi
from pathlib import Path
from utils.mongo import MongoDB
import mystbin
import time
from utils.errors import Blacklisted
import asyncio

async def prefix(avimetrybot, message):
    if not message.guild:
        return "a."
    try:
        data=await avimetrybot.config.find(message.guild.id)
        if message.content.lower().startswith(data["prefix"]):
            try:
                lower=message.content[:len(data["prefix"])]
                return lower
            except Exception:
                return data["prefix"]
        if not data or "prefix" not in data:
            return "a."
        return data["prefix"]
    except:
        return "a."

allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=True, replied_user=False)
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
        self.commands_ran=0
        self.session=aiohttp.ClientSession()
        self.cog_cooldown=commands.CooldownMapping.from_cooldown(2, 10, commands.BucketType.member)
        # pylint: disable=unused-variable
        @self.check
        async def globally_block_dms(ctx):
            if not ctx.guild:
                raise commands.NoPrivateMessage("Commands do not work in dm channels.")
            return True
        
        @self.check
        async def block(ctx):
            find_blacklist=await self.bot_users.find(ctx.author.id)
            try:
                check=find_blacklist["blacklisted"]
                if check==True:
                    raise Blacklisted
            except KeyError:
                pass
            return True
        
        
        @self.event
        async def on_ready():
            timenow=datetime.datetime.now().strftime("%I:%M %p")
            print('------\n'
            'Succesfully logged in. Bot Info Below:\n'
            f'Username: {self.user.name}\n'
            f'Bot ID: {self.user.id}\n'
            f'Login Time: {datetime.date.today()} at {timenow}\n'
            '------')

            await asyncio.sleep(5)
            self.mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('DB_Token'))
            self.db=self.mongo['avimetry']
            self.config=MongoDB(self.db, 'new')
            self.mutes=MongoDB(self.db, 'mutes')
            self.logs=MongoDB(self.db, 'logging')
            self.bot_users=MongoDB(self.db, 'users')
            
            current_mutes=await self.mutes.get_all()
            for mute in current_mutes:
                self.muted_users[mute["_id"]] = mute
            

        # pylint: enable=unused-variable
        os.environ["JISHAKU_HIDE"] = "True"
        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
        os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 
        #self.load_extension('jishaku')
        for filename in os.listdir('./avimetrybot/cogs'):
            if filename.endswith('.py'):
                self.load_extension(f'cogs.{filename[:-3]}')

    async def get_context(self, message, *, cls=AvimetryContext):
        return await super().get_context(message, cls=cls)

    async def api_latency(self, ctx):
        start=time.perf_counter()
        await ctx.trigger_typing()
        end=time.perf_counter()
        return round((end-start)*1000)

    async def database_latency(self, ctx):
        start=time.perf_counter()
        await self.config.find({"_id":ctx.guild.id})
        end=time.perf_counter()
        return round((end-start)*1000)

    async def close(self):
        self.mongo.close()
        await self.sr.close()
        await self.zaneapi.close()
        await self.myst.close()
        await self.session.close()
        print('\nClosing Connection to Discord.')
        await super().close()
        
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.id in self.owner_ids:
            await self.process_commands(after)