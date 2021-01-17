import discord
import os
import asyncio
import datetime
import pymongo
from pymongo import MongoClient
from discord.ext import commands, tasks
from dotenv import load_dotenv
from utils.mongo import Document
import motor.motor_asyncio

#Get Bot Token
load_dotenv()
avitoken = os.getenv('Bot_Token')

#Command Prefix and Intents
async def prefix(client, message):
    if not message.guild:
        return [str("a.")]
    try:
        data=await avimetry.config.find(message.guild.id)
        if not data or "prefix" not in data:
            return "a."
        return data["prefix"]
    except:
        return "a."
allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=False)
intents=discord.Intents.all()
avimetry = commands.Bot(command_prefix = prefix, case_insensitive=True, intents=intents, allowed_mentions=allowed_mentions)
avimetry.launch_time=datetime.datetime.utcnow()

#Database 
avimetry.cluster=MongoClient(os.getenv('DB_Token'))
avimetry.db=avimetry.cluster['avimetry']
avimetry.collection=avimetry.db['new']
avimetry.mutes=avimetry.collection.find_one({"_id":"mutes"})
avimetry.muted_users={}

#No Commands in DMs
@avimetry.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

#Reload main cogs 
@tasks.loop(minutes=5)
async def load_important():
    try:
        avimetry.load_extension('jishaku')
        avimetry.load_extension("cogs.loads")
    except commands.ExtensionAlreadyLoaded:
        return

@avimetry.event
async def on_ready():
    load_important.start()
    avimetry.mongo = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('DB_Token'))
    avimetry.db=avimetry.mongo['avimetry']
    avimetry.config=Document(avimetry.db, 'new')
    avimetry.mutes=Document(avimetry.db, 'mutes')
    
    current_mutes=await avimetry.mutes.get_all()
    for mute in current_mutes:
        avimetry.muted_users[mute["_id"]] = mute

#Load Cogs
avimetry.load_extension('jishaku')
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True" 
for filename in os.listdir('./avimetrybot/cogs'):
    if filename.endswith('.py'):
        avimetry.load_extension(f'cogs.{filename[:-3]}')

#Log-In
avimetry.run(avitoken)