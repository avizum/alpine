from discord.ext import commands

from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES

class CustomDebugCog(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    pass

def setup(avimetry: commands.Bot):
    avimetry.add_cog(CustomDebugCog(bot=avimetry))