import discord
import os
import datetime
import pymongo
from pymongo import MongoClient
from discord.ext import commands, tasks
from dotenv import load_dotenv
from utils.mongo import MongoDB
import motor.motor_asyncio
import pathlib

#Get Bot Token
load_dotenv()
avitoken = os.getenv('Bot_Token')

#Command Prefix and Intents
async def prefix(client, message):
    if not message.guild:
        return "a."
    try:
        data=await avimetry.config.find(message.guild.id)
        if not data or "prefix" not in data:
            await avimetry.config.upsert({"_id": message.guild.id, "prefix": "a."})
            await message.channel.send("No prefix found for this server, so I set it as **a.**")
        return data["prefix"]
    except:
        return "a."
allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True, replied_user=False)
intents=discord.Intents.all()
activity=discord.Game('avimetry() | a.help')
avimetry = commands.Bot(command_prefix = prefix, case_insensitive=True, intents=intents, allowed_mentions=allowed_mentions, activity=activity)



#Bot Vars
avimetry.launch_time=datetime.datetime.utcnow()
avimetry.muted_users={}
avimetry.devmode=False

#No Commands in DMs
@avimetry.check
async def globally_block_dms(ctx):
    if not ctx.guild:
        raise commands.NoPrivateMessage("Commands do not work in dm channels.")
    return True

#Reload main cogs 
@tasks.loop(seconds=1)
async def load_important():
    loader=('jishaku', 'owner')
    for load in loader:
        ext = "cogs." if load != "jishaku" else ""
        try:
            avimetry.load_extension(f"{ext}{load}")
        except:
            pass

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
        print(f"Loaded {filename[:-3]}")

total = 0
file_amount = 0
ENV = "env"
for path, _, files in os.walk("."):
    for name in files:
        file_dir = str(pathlib.PurePath(path, name))
        if not name.endswith(".py") or ENV in file_dir:
            continue
        file_amount += 1
        with open(file_dir, "r", encoding="utf-8") as file:
            for line in file:
                if not line.strip().startswith("#") or not line.strip():
                    total += 1
avimetry.description=f"avimetry() is a bot that has with **{file_amount}** python files and **{total}** lines of code."

#Log-In
avimetry.run(avitoken)