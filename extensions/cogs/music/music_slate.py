import slate
import core
from core import Bot, Context
import spotipy


class SMusic(core.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.node = None

    @core.command(name="sconnect", aliases=["sjoin"])
    async def connect(self, ctx: Context):
        await ctx.author.voice.channel.connect(cls=slate.Player())
        await ctx.send("jo")

    @core.command(name="sdisconnect", aliases=["sleave"])
    async def disconnect(self, ctx: Context):
        await ctx.voice_client.disconnect()

    @core.command(name="splay")
    async def play(self, ctx: Context, *, query: str):
        """
        Play a song.
        """
        vc: slate.Player = ctx.voice_client
        search = await vc.node.search(query, source=slate.Source.NONE, ctx=ctx)
        await vc.play(search.result[0])

async def setup(bot: Bot) -> None:
    await bot.add_cog(SMusic(bot))
