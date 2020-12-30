import discord
from discord.ext import commands
import random
import asyncio
import json
import datetime

class AutoMod(commands.Cog):
    
    def __init__(self, avibot):
        self.avibot = avibot
        
def setup(avibot):
    avibot.add_cog(AutoMod(avibot))


