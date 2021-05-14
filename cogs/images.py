"""
Cool things you can do with images.
Copyright (C) 2021 avizum

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
import io
import typing
from discord.ext import commands
from io import BytesIO
from asyncdagpi import ImageFeatures
from twemoji_parser import emoji_to_url as urlify_emoji
from utils import AvimetryBot, AvimetryContext, GetAvatar

embed = discord.Embed()
args = typing.Union[discord.Member, discord.PartialEmoji, discord.Emoji, str, None]


class Image(commands.Cog, name="Images"):
    '''
    Commands for image manipuation and more.
    '''
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    async def do_dagpi(self, ctx: AvimetryContext, feature: ImageFeatures, argument, gif: bool = False):
        converter = GetAvatar()
        image = await converter.convert(ctx, argument)
        if image is None:
            if ctx.message.attachments:
                img = ctx.message.attachments[0]
                image = img.url
            else:
                image = str(ctx.author.avatar_url_as(format="png", static_format="png", size=1024))
        else:
            image = image
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(feature, image)
        file = discord.File(fp=image.image, filename=f"{ctx.command.name}.{'gif' if gif is True else 'png'}")
        return file

    async def do_zane(self, ctx: AvimetryContext, method, argument, gif: bool = False):
        converter = GetAvatar()
        image = await converter.convert(ctx, argument)
        if image is None:
            if ctx.message.attachments:
                img = ctx.message.attachments[0]
                image = img.url
            else:
                image = str(ctx.author.avatar_url_as(format="png", static_format="png", size=1024))
        else:
            image = image
        image = await method(argument)
        file = discord.File(fp=image, filename=f"{ctx.command.name}.{'gif' if gif is True else 'png'}")
        return file

    async def do_embed(self, ctx, file: discord.File):
        url = f"attachment://{file.filename}"
        embed.set_image(url=url)
        await ctx.send(file=file, embed=embed)

    @commands.command(name="pixel")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_pixel(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.pixel(), item, False)
        await self.do_embed(ctx, meth)

    @commands.command(name="triggered")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_triggered(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.triggered(), item, True)
        await self.do_embed(ctx, meth)

    @commands.command(name="5g1g")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_5g1g(self, ctx, item1: GetAvatar, item2: GetAvatar):
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(ImageFeatures.five_guys_one_girl(), url=item1, url2=item2)
        file = discord.File(fp=image.image, filename="5g1g.png")
        await self.do_embed(ctx, file)

    @commands.command(name="whyareyougay", aliases=["wayg"])
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_wayg(self, ctx, item1: GetAvatar, item2: GetAvatar):
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(ImageFeatures.why_are_you_gay(), url=item1, url2=item2)
        file = discord.File(fp=image.image, filename="why_are_you_gay.png")
        await self.do_embed(ctx, file)

    @commands.command(name="tweet")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_tweet(self, ctx, user: GetAvatar, username: str, *, text: str):
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(ImageFeatures.tweet(), text=text, url=user, username=username)
        file = discord.File(fp=image.image, filename="tweet.png")
        await self.do_embed(ctx, file)

    @commands.command(name="discord")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_discord(self, ctx, user: discord.User = None, *, text: str = None):
        user_name = None
        if text is None:
            url = str(ctx.author.avatar_url_as(format="png", static_format="png", size=1024))
            text = "I am an idiot for not putting the text in"
            user_name = ctx.author.name
        else:
            url = str(user.avatar_url_as(format="png", static_format="png", size=1024))
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(
                ImageFeatures.discord(), text=text, url=url,
                username=user.name if user_name is None else user_name)
        file = discord.File(fp=image.image, filename="discord.png")
        await self.do_embed(ctx, file)

    @commands.command(name="youtube")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_youtube(self, ctx, user: discord.Member = None, *, text: str = None):
        user_name = None
        if text is None:
            url = str(ctx.author.avatar_url_as(format="png", static_format="png", size=1024))
            text = "I am an idiot for not putting the text in"
            user_name = ctx.author.name
        else:
            url = str(user.avatar_url_as(format="png", static_format="png", size=1024))
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(
                ImageFeatures.youtube(), text=text, url=url,
                username=user.name if user_name is None else user_name)
        file = discord.File(fp=image.image, filename="youtube.png")
        await self.do_embed(ctx, file)

    @commands.command(name="america")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_america(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.america(), item, True)
        await self.do_embed(ctx, meth)

    @commands.command(name="communism")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_communism(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.communism(), item, True)
        await self.do_embed(ctx, meth)

    @commands.command(name="colors")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_colors(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.colors(), item)
        await self.do_embed(ctx, meth)

    @commands.command(name="wasted")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_wasted(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.wasted(), item)
        await self.do_embed(ctx, meth)

    @commands.command(name="hitler")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_hitler(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.hitler(), item)
        await self.do_embed(ctx, meth)

    @commands.command(name="satan")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_satan(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.satan(), item)
        await self.do_embed(ctx, meth)

    @commands.command(name="delete")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_delete(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.delete(), item)
        await self.do_embed(ctx, meth)

    @commands.command(name="wanted")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_wanted(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.wanted(), item)
        await self.do_embed(ctx, meth)

    @commands.command(name="jail")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_jail(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.jail(), item)
        await self.do_embed(ctx, meth)

    @commands.command(name="ascii")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_ascii(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.ascii(), item)
        await self.do_embed(ctx, meth)

    # Magic Command
    @commands.command(
        enabled=False,
        usage="[url or member]",
        brief="Returns a gif of your image being scaled",
        aliases=["magik", "magick"]
    )
    async def magic(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_zane(ctx, self.avi.zane.magic, item, True)
        await self.do_embed(ctx, meth)

    # Floor Command
    @commands.command(
        enabled=False,
        usage="[url or member]",
        brief="Returns a gif of your image being bent into a floor",
    )
    async def floor(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            floor = await self.avi.zaneapi.floor(str(url))
            file = discord.File(io.BytesIO(floor.read()), filename="floor.gif")
            embed.set_image(url="attachment://floor.gif")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False,
        usage="[url or member]", brief="Retruns text of the provided image"
    )
    async def braille(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            braille = await self.avi.zaneapi.braille(str(url))
            return await ctx.send_raw(f"```{braille}```")

    @commands.command(enabled=False, usage="[url or member]", brief="Returns your image deepfried")
    async def deepfry(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            deepfry = await self.avi.zaneapi.deepfry(str(url))
            file = discord.File(BytesIO(deepfry.read()), filename="deepfry.png")
            embed.set_image(url="attachment://deepfry.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False, usage="[url or member]", brief="Returns your image with black and white dots"
    )
    async def dots(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            dots = await self.avi.zaneapi.dots(str(url))
            file = discord.File(BytesIO(dots.read()), filename="dots.png")
            embed.set_image(url="attachment://dots.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False,
        usage="[url or member]",
        brief="Returns your image heavilly compressed and with low quality, just like jpeg",
    )
    async def jpeg(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            jpeg = await self.avi.zaneapi.jpeg(str(url))
            file = discord.File(BytesIO(jpeg.read()), filename="jpeg.png")
            embed.set_image(url="attachment://jpeg.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False,
        usage="[url or member]", brief="Returns a gif of all the pixels spreading out"
    )
    async def spread(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            spread = await self.avi.zaneapi.spread(str(url))
            file = discord.File(BytesIO(spread.read()), filename="spread.gif")
            embed.set_image(url="attachment://spread.gif")
            await ctx.send(file=file, embed=embed)

    @commands.command(enabled=False, usage="[url or member]", brief="Returns your image on a cube")
    async def cube(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            cube = await self.avi.zaneapi.cube(str(url))
            file = discord.File(io.BytesIO(cube.read()), filename="cube.png")
            embed.set_image(url="attachment://cube.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(enabled=False, usage="[url or member]", brief="Returns the pixels on your image")
    async def sort(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            sort = await self.avi.zaneapi.sort(str(url))
            file = discord.File(BytesIO(sort.read()), filename="sort.png")
            embed.set_image(url="attachment://sort.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False,
        usage="[url or member]", brief="Returns up to 8 colors from your image"
    )
    async def palette(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            palette = await self.avi.zaneapi.palette(str(url))
            file = discord.File(BytesIO(palette.read()), filename="palette.png")
            embed.set_image(url="attachment://palette.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False,
        usage="[url or member]", brief="Returns an inverted version of your image"
    )
    async def invert(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            invert = await self.avi.zaneapi.invert(str(url))
            file = discord.File(BytesIO(invert.read()), filename="invert.png")
            embed.set_image(url="attachment://invert.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False,
        usage="[url or member]", brief="Returns a poserized version of your image"
    )
    async def posterize(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            posterize = await self.avi.zaneapi.posterize(str(url))
            file = discord.File(BytesIO(posterize.read()), filename="posterize.png")
            embed.set_image(url="attachment://posterize.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(enabled=False, usage="[url or member]", brief="Returns your image as grayscale")
    async def grayscale(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            grayscale = await self.avi.zaneapi.grayscale(str(url))
            file = discord.File(BytesIO(grayscale.read()), filename="grayscale.png")
            embed.set_image(url="attachment://grayscale.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False,
        usage="[url or member]",
        brief="Returns an your image scaled down then scaled back up",
    )
    async def pixelate(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            pixelate = await self.avi.zaneapi.pixelate(str(url))
            file = discord.File(BytesIO(pixelate.read()), filename="pixelate.png")
            embed.set_image(url="attachment://pixelate.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False,
        usage="[url or member]", brief="Returns a gif of your image being swirled"
    )
    async def swirl(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            swirl = await self.avi.zaneapi.swirl(str(url))
            file = discord.File(BytesIO(swirl.read()), filename="swirl.gif")
            embed.set_image(url="attachment://swirl.gif")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        enabled=False,
        usage="[url or member]", brief="Returns your image with a sobel filter"
    )
    async def sobel(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            sobel = await self.avi.zaneapi.sobel(str(url))
            file = discord.File(BytesIO(sobel.read()), filename="sobel.png")
            embed.set_image(url="attachment://sobel.png")
            await ctx.send(file=file, embed=embed)

    @commands.command()
    async def animal(self, ctx: AvimetryContext, animal):
        async with ctx.channel.typing():
            e = await self.avi.sr.get_image(animal)
            file = discord.File(BytesIO(await e.read()), filename="animal.png")
            embed.set_image(url="attachment://animal.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(brief="Convert emoji to url so you can download them")
    async def emojiurl(self, ctx: AvimetryContext, emoji):
        result = await urlify_emoji(emoji)
        await ctx.send(result)


def setup(avi):
    avi.add_cog(Image(avi))


"""todo
        import io
        floor=bot.sr.filter("triggered", str(ctx.author.avatar_url_as(format="png")))
        file=discord.File(io.BytesIO(await floor.read()), filename="magic.gif")
        await ctx.send(file=file)



        import io
        floor=bot.sr.youtube_comment(str(ctx.author.avatar_url_as(format="png")), ctx.author.name, "asd")
        file=discord.File(io.BytesIO(await floor.read()), filename="magic.png")
        await ctx.send(file=file)
"""
