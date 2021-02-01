import discord
import os
import asyncio
import datetime
import pymongo
from pymongo import MongoClient
from discord.ext import commands, tasks
from dotenv import load_dotenv
from utils.mongo import MongoDB
import motor.motor_asyncio

#Get Bot Token
load_dotenv()
avitoken = os.getenv('Bot_Token')

#Command Prefix and Intents
async def prefix(client, message):
    if avimetry.devmode==True:
        if message.author.id in avimetry.owner_ids:
            return ""
    if not message.guild:
        return [str("a.")]
    try:
        data=await avimetry.config.find(message.guild.id)
        if not data or "prefixs" not in data:
            await avimetry.config.upsert({"_id": message.guild.id, "prefix": "a."})
        return data["prefixs"]
    except:
        return "aa."
allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=False)
intents=discord.Intents.all()
avimetry = commands.Bot(command_prefix = prefix, case_insensitive=True, intents=intents, allowed_mentions=allowed_mentions)

#Bot Vars
avimetry.launch_time=datetime.datetime.utcnow()
avimetry.muted_users={}
avimetry.devmode=False

#No Commands in DMs
@avimetry.check
async def globally_block_dms(ctx):
    if not ctx.guild:
        raise commands.NoPrivateMessage("Commands do not work in dm channels.")
    else:
        return True

#Reload main cogs 
@tasks.loop(minutes=5)
async def load_important():
    try:
        avimetry.load_extension('jishaku')
        avimetry.load_extension("cogs.owner")
    except commands.ExtensionAlreadyLoaded:
        return

@avimetry.event
async def on_ready():
    load_important.start()
    avimetry.mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('DB_Token'))
    avimetry.db=avimetry.mongo['avimetry']
    avimetry.config=MongoDB(avimetry.db, 'new')
    avimetry.mutes=MongoDB(avimetry.db, 'mutes')
    avimetry.logs=MongoDB(avimetry.db, 'logging')
    
    current_mutes=await avimetry.mutes.get_all()
    for mute in current_mutes:
        avimetry.muted_users[mute["_id"]] = mute
        
#Load Cogs
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 
avimetry.load_extension('jishaku')
for filename in os.listdir('./avimetrybot/cogs'):
    if filename.endswith('.py'):
        avimetry.load_extension(f'cogs.{filename[:-3]}')

#Log-In
avimetry.run(avitoken)