from discord.ext import commands

from jishaku.cog import STANDARD_FEATURES, OPTIONAL_FEATURES


class JishakuCog(*OPTIONAL_FEATURES, *STANDARD_FEATURES):
    """
    Jishaku best thing evar
    """
    pass


def setup(avi: commands.Bot):
    avi.add_cog(JishakuCog(bot=avi))
