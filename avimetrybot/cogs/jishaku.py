import discord
from discord.ext import commands
import asyncio
# pylint: disable=no-name-in-module, import-error
from jishaku.features.baseclass import Feature
from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES

class JishakuCog(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    pass


def setup(avimetry: commands.Bot):
    avimetry.add_cog(JishakuCog(bot=avimetry))