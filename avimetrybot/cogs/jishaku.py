from discord.ext import commands

from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES


class Jishaku(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """
    Owner only commands.
    """
    pass


def setup(avi: commands.Bot):
    avi.add_cog(Jishaku(bot=avi))
