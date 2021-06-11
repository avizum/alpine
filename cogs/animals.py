import discord

from io import BytesIO
from utils import AvimetryContext, AvimetryBot
from discord.ext import commands


class Animals(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    async def do_animal(self, ctx: AvimetryContext, animal: str):
        e = await self.avi.sr.get_image(animal)
        file = discord.File(BytesIO(await e.read()), filename=f"{animal}.png")
        embed = discord.Embed(title=f"Here is {animal}", description="Powered by Some Random API")
        embed.set_image(url=f"attachment://{animal}.png")
        await ctx.send(file=file, embed=embed)

    @commands.command()
    async def dog(self, ctx: AvimetryContext):
        await self.do_animal(ctx, "dog")

    @commands.command()
    async def cat(self, ctx: AvimetryContext):
        await self.do_animal(ctx, "cat")

    @commands.command()
    async def panda(self, ctx: AvimetryContext):
        await self.do_animal(ctx, "panda")

    @commands.command()
    async def fox(self, ctx: AvimetryContext):
        await self.do_animal(ctx, "fox")

    @commands.command()
    async def koala(self, ctx: AvimetryContext):
        await self.do_animal(ctx, "koala")

    @commands.command()
    async def birb(self, ctx: AvimetryContext):
        await self.do_animal(ctx, "birb")

    @commands.command()
    async def racoon(self, ctx: AvimetryContext):
        await self.do_animal(ctx, "racoon")

    @commands.command()
    async def kangaroo(self, ctx: AvimetryContext):
        await self.do_animal(ctx, "kangaroo")


def setup(avi: AvimetryBot):
    avi.add_cog(Animals(avi))
