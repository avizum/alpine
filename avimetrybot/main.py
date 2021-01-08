import discord
import os
import asyncio
import json
import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv
from discord.ext import menus

#Get Bot Token
load_dotenv()
avitoken = os.getenv('Bot_Token')

#Command Prefix and Intents
def prefix(client, message):
    if message.guild is None:
        return [str("a.")]
    else:
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
            pre = prefixes[str(message.guild.id)]
        return pre
avimetry = commands.Bot(command_prefix = prefix, case_insensitive=True, intents=discord.Intents.all())
avimetry.launch_time = datetime.datetime.utcnow()

#No Commands in DMs
@avimetry.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

#Reload main cogs 
@tasks.loop(minutes=5)
async def loop():
    try:
        avimetry.load_extension('jishaku')
        avimetry.load_extension("cogs.loads")
    except commands.ExtensionAlreadyLoaded:
        return
loop.start()

#Load Cogs
avimetry.load_extension('jishaku')
os.environ["JISHAKU_HIDE"] = "True"
for filename in os.listdir('./avimetrybot/cogs'):
    if filename.endswith('.py'):
        avimetry.load_extension(f'cogs.{filename[:-3]}')

#Log-In
avimetry.run(avitoken, bot=True)