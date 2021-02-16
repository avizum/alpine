import discord
from discord.ext import commands
import aiozaneapi
import aiohttp
from io import BytesIO
import io
import re
from twemoji_parser import emoji_to_url as urlify_emoji
from PIL import Image
import typing

embed=discord.Embed()
embed.set_footer(text="Powered by ZaneApi")
regex_url=re.compile(r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})")
# pylint: disable=unsubscriptable-object
args=typing.Union[discord.Member, discord.PartialEmoji, discord.Emoji, str, None] 
# pylint: enable=unsubscriptable-object
class Manipulation(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry=avimetry

    async def member_convert(self, ctx, url):
        if url==None:
            url=ctx.author.avatar_url_as(format="png")

        elif isinstance(url, discord.Member):
            url=url.avatar_url_as(format="png")

        elif isinstance(url, discord.PartialEmoji) or isinstance(url, discord.Emoji):
            url=url.url
        else:
            find_url=re.findall(regex_url, url)
            if find_url:
                url="".join(find_url)
            else:
                url=await urlify_emoji(url)
        return url

#Magic Command
    @commands.command(usage="[url or member]", brief="Returns a gif of your image being scaled")
    async def magic(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            magic=await self.avimetry.zaneapi.magic(str(url))
            file=discord.File(io.BytesIO(magic.read()), filename="magic.gif")
            embed.set_image(url="attachment://magic.gif")
            await ctx.send(file=file, embed=embed)

#Floor Command
    @commands.command(usage="[url or member]", brief="Returns a gif of your image being bent into a floor")
    async def floor(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            floor=await self.avimetry.zaneapi.floor(str(url))
            file=discord.File(io.BytesIO(floor.read()), filename="floor.gif")
            embed.set_image(url="attachment://floor.gif")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Retruns text of the provided image")
    async def braille(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            braille=await self.avimetry.zaneapi.braille(str(url))
            return await ctx.send(f"```{braille}```")

    @commands.command(usage="[url or member]", brief="Returns your image deepfried")
    async def deepfry(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            deepfry=await self.avimetry.zaneapi.deepfry(str(url))
            file=discord.File(BytesIO(deepfry.read()), filename="deepfry.png")
            embed.set_image(url="attachment://deepfry.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns your image with black and white dots")
    async def dots(self, ctx, url:args):    
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            dots=await self.avimetry.zaneapi.dots(str(url))
            file=discord.File(BytesIO(dots.read()), filename="dots.png")
            embed.set_image(url="attachment://dots.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns your image heavilly compressed and with low quality, just like jpeg")
    async def jpeg(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            jpeg=await self.avimetry.zaneapi.jpeg(str(url))
            file=discord.File(BytesIO(jpeg.read()), filename="jpeg.png")
            embed.set_image(url="attachment://jpeg.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns a gif of all the pixels spreading out")
    async def spread(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            spread=await self.avimetry.zaneapi.spread(str(url))
            file=discord.File(BytesIO(spread.read()), filename="spread.gif")
            embed.set_image(url="attachment://spread.gif")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns your image on a cube")
    async def cube(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            cube=await self.avimetry.zaneapi.cube(str(url))
            file=discord.File(io.BytesIO(cube.read()), filename="cube.png")
            embed.set_image(url="attachment://cube.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns the pixels on your image")
    async def sort(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            sort=await self.avimetry.zaneapi.sort(str(url))
            file=discord.File(BytesIO(sort.read()), filename="sort.png")
            embed.set_image(url="attachment://sort.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns up to 8 colors from your image")
    async def palette(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            palette=await self.avimetry.zaneapi.palette(str(url))
            file=discord.File(BytesIO(palette.read()), filename="palette.png")
            embed.set_image(url="attachment://palette.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns an inverted version of your image")
    async def invert(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            invert=await self.avimetry.zaneapi.invert(str(url))
            file=discord.File(BytesIO(invert.read()), filename="invert.png")
            embed.set_image(url="attachment://invert.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns a poserized version of your image")
    async def posterize(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            posterize=await self.avimetry.zaneapi.posterize(str(url))
            file=discord.File(BytesIO(posterize.read()), filename="posterize.png")
            embed.set_image(url="attachment://posterize.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns your image as grayscale")
    async def grayscale(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            grayscale=await self.avimetry.zaneapi.grayscale(str(url))
            file=discord.File(BytesIO(grayscale.read()), filename="grayscale.png")
            embed.set_image(url="attachment://grayscale.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns an your image scaled down then scaled back up")
    async def pixelate(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            pixelate=await self.avimetry.zaneapi.pixelate(str(url))
            file=discord.File(BytesIO(pixelate.read()), filename="pixelate.png")
            embed.set_image(url="attachment://pixelate.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns a gif of your image being swirled")
    async def swirl(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            swirl=await self.avimetry.zaneapi.swirl(str(url))
            file=discord.File(BytesIO(swirl.read()), filename="swirl.gif")
            embed.set_image(url="attachment://swirl.gif")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns your image with a sobel filter")
    async def sobel(self, ctx, url:args):
        url=await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            sobel=await self.avimetry.zaneapi.sobel(str(url))
            file=discord.File(BytesIO(sobel.read()), filename="sobel.png")
            embed.set_image(url="attachment://sobel.png")
            await ctx.send(file=file, embed=embed)      
def setup(avimetry):
    avimetry.add_cog(Manipulation(avimetry))