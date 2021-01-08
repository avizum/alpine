import discord
from discord.ext import commands
import sys
import traceback

class testing(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry

def setup(avimetry):
    avimetry.add_cog(testing(avimetry))
