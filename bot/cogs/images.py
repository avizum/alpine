import discord
from discord.ext import commands
from io import BytesIO
import io
import re
from asyncdagpi import ImageFeatures
from twemoji_parser import emoji_to_url as urlify_emoji
from utils.context import AvimetryContext
import typing

embed = discord.Embed()
regex_url = re.compile(
    r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+"
    r"[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
)
emoji_regex = r"<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]{2,32}):(?P<id>[0-9]{18,22})>"
args = typing.Union[discord.Member, discord.PartialEmoji, discord.Emoji, str, None]


class GetAvatar(commands.Converter):
    async def convert(self, ctx: AvimetryContext, argument: str = None):
        try:
            member_converter = commands.MemberConverter()
            member = await member_converter.convert(ctx, argument)
            image = member.avatar_url_as(format="png", static_format="png", size=1024)
            return str(image)
        except Exception:
            try:
                url = await urlify_emoji(argument)
                if re.match(regex_url, url):
                    image = str(url)
                    return image
                if re.match(regex_url, argument):
                    image = argument
                    return image
                if re.match(emoji_regex, argument):
                    emoji_converter = commands.EmojiConverter()
                    emoji = emoji_converter.convert(ctx, argument)
                    image = emoji.url_as(format="png", static_format="png", size=1024)
                    return image
            except Exception:
                return None
        raise commands.MemberNotFound(argument)


async def image(ctx: AvimetryContext, argument: str):
    avatar = GetAvatar()
    url = avatar.convert(ctx, argument)
    if url is not None:
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            url = attachment.url


class Manipulation(commands.Cog):
    '''
    Commands to manipulate images.
    '''
    def __init__(self, avi):
        self.avi = avi

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

    @commands.command(name="pixel")
    async def dag_pixel(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.pixel(), item, False)
        await ctx.send(file=meth)

    @commands.command(name="triggered")
    async def dag_triggered(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.triggered(), item, True)
        await ctx.send(file=meth)

    @commands.command(name="5g1g")
    async def dag_5g1g(self, ctx, item1: GetAvatar, item2: GetAvatar):
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(ImageFeatures.five_guys_one_girl(), url=item1, url2=item2)
        file = discord.File(fp=image.image, filename="5g1g.png")
        await ctx.send(file=file)

    @commands.command(name="whyareyougay", aliases=["wayg"])
    async def dag_wayg(self, ctx, item1: GetAvatar, item2: GetAvatar):
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(ImageFeatures.why_are_you_gay(), url=item1, url2=item2)
        file = discord.File(fp=image.image, filename="why_are_you_gay.png")
        await ctx.send(file=file)

    @commands.command(name="tweet")
    async def dag_tweet(self, ctx, user: GetAvatar, *, text: str):
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(ImageFeatures.tweet(), text=text, url=user, username=user.name)
        file = discord.File(fp=image.image, filename="tweet.png")
        await ctx.send(file=file)

    @commands.command(name="discord")
    async def dag_discord(self, ctx, user: GetAvatar, *, text: str):
        async with ctx.channel.typing():
            image = await self.avi.dagpi.image_process(ImageFeatures.discord(), text=text, url=user, username=user.name)
        file = discord.File(fp=image.image, filename="tweet.png")
        await ctx.send(file=file)

    @commands.command(name="america")
    async def dag_america(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.america(), item, True)
        await ctx.send(file=meth)

    @commands.command(name="communism")
    async def dag_communism(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.communism(), item, True)
        await ctx.send(file=meth)

    @commands.command(name="colors")
    async def dag_colors(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.colors(), item)
        await ctx.send(file=meth)

    @commands.command(name="wasted")
    async def dag_wasted(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.wasted(), item)
        await ctx.send(file=meth)

    @commands.command(name="hitler")
    async def dag_hitler(self, ctx, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.hitler(), item)
        await ctx.send(file=meth)

    # Magic Command
    @commands.command(
        usage="[url or member]",
        brief="Returns a gif of your image being scaled",
        aliases=["magik", "magick"]
    )
    async def magic(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_zane(ctx, self.avi.zane.magic, item, True)
        await ctx.send(file=meth)

    # Floor Command
    @commands.command(
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
        usage="[url or member]", brief="Retruns text of the provided image"
    )
    async def braille(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            braille = await self.avi.zaneapi.braille(str(url))
            return await ctx.send_raw(f"```{braille}```")

    @commands.command(usage="[url or member]", brief="Returns your image deepfried")
    async def deepfry(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            deepfry = await self.avi.zaneapi.deepfry(str(url))
            file = discord.File(BytesIO(deepfry.read()), filename="deepfry.png")
            embed.set_image(url="attachment://deepfry.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
        usage="[url or member]", brief="Returns your image with black and white dots"
    )
    async def dots(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            dots = await self.avi.zaneapi.dots(str(url))
            file = discord.File(BytesIO(dots.read()), filename="dots.png")
            embed.set_image(url="attachment://dots.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
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
        usage="[url or member]", brief="Returns a gif of all the pixels spreading out"
    )
    async def spread(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            spread = await self.avi.zaneapi.spread(str(url))
            file = discord.File(BytesIO(spread.read()), filename="spread.gif")
            embed.set_image(url="attachment://spread.gif")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns your image on a cube")
    async def cube(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            cube = await self.avi.zaneapi.cube(str(url))
            file = discord.File(io.BytesIO(cube.read()), filename="cube.png")
            embed.set_image(url="attachment://cube.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns the pixels on your image")
    async def sort(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            sort = await self.avi.zaneapi.sort(str(url))
            file = discord.File(BytesIO(sort.read()), filename="sort.png")
            embed.set_image(url="attachment://sort.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
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
        usage="[url or member]", brief="Returns a poserized version of your image"
    )
    async def posterize(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            posterize = await self.avi.zaneapi.posterize(str(url))
            file = discord.File(BytesIO(posterize.read()), filename="posterize.png")
            embed.set_image(url="attachment://posterize.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(usage="[url or member]", brief="Returns your image as grayscale")
    async def grayscale(self, ctx: AvimetryContext, url: args):
        url = await self.member_convert(ctx, url)
        async with ctx.channel.typing():
            grayscale = await self.avi.zaneapi.grayscale(str(url))
            file = discord.File(BytesIO(grayscale.read()), filename="grayscale.png")
            embed.set_image(url="attachment://grayscale.png")
            await ctx.send(file=file, embed=embed)

    @commands.command(
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
    avi.add_cog(Manipulation(avi))


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
