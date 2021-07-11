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
import typing
from discord.ext import commands
from asyncdagpi import ImageFeatures, Image
from twemoji_parser import emoji_to_url
from utils import AvimetryBot, AvimetryContext, GetAvatar

embed = discord.Embed()
args = typing.Union[discord.Member, discord.PartialEmoji, discord.Emoji, str, None]


class Image(commands.Cog, name="Images"):
    '''
    Commands for image manipuation and more.
    '''
    def __init__(self, bot: AvimetryBot):
        self.bot = bot

    async def do_dagpi(self, ctx: AvimetryContext, feature: ImageFeatures, argument, gif: bool = False):
        converter = GetAvatar()
        image = await converter.convert(ctx, argument)
        if image is None:
            if ctx.message.attachments:
                img = ctx.message.attachments[0]
                image = img.url
            else:
                image = str(ctx.author.avatar_url_as(format="png", static_format="png", size=1024))
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(feature, image)
        return image

    async def dag_embed(self, ctx: AvimetryContext, image: Image, title: str):
        embed = discord.Embed(
            title=title.title(),
            description=(
                f"Image processed in `{float(image.process_time) * 1000:.2f}ms`\n"
                "This command is powered by [Dagpi](https://dagpi.xyz)"
            )
        )
        dag_image = discord.File(fp=image.image, filename=f"{title}.{image.format}")
        url = f"attachment://{dag_image.filename}"
        embed.set_image(url=url)
        await ctx.send(file=dag_image, embed=embed)

    async def do_embed(self, ctx, file: discord.File):
        url = f"attachment://{file.filename}"
        embed.set_image(url=url)
        await ctx.send(file=file, embed=embed)

    @commands.command(name="pixel")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_pixel(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.pixel(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="colors")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_colors(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.colors(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="america")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_america(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.america(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="communism")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_communism(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.communism(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="triggered")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_triggered(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.triggered(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="wasted")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_wasted(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.wasted(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="invert")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_invert(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.invert(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="sobel")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_sobel(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.sobel(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="hog")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_hog(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.hog(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="triangle")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_triangle(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.triangle(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="blur")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_blur(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.blur(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="rgb")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_rgb(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.rgb(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="angel")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_angel(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.angel(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="satan")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_satan(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.satan(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="delete")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_delete(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.delete(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="fedora")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_fedora(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.fedora(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="hitler")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_hitler(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.hitler(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="wanted")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_wanted(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.wanted(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="stringify")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_stringify(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.stringify(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="mosaic")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_mosaic(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.mosiac(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="sithlord")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_sithlord(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.sith(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="jail")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_jail(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.jail(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="pride", enabled=False)
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_pride(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.pride(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="dgay", enabled=False)
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_gay(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.gay(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="trash")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_trash(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.trash(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="deepfry")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_deepfry(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.deepfry(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="ascii")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_ascii(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.ascii(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="charcoal")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_charcoal(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.charcoal(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="posterize")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_posterize(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.poster(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="sepia")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_sepia(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.sepia(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="swirl")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_swirl(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.swirl(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="paint")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_paint(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.paint(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="night")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_night(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.night(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="rainbow")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_rainbow(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.rainbow(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="magic", aliases=["magick", "magik"])
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_magic(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.magik(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="5g1g")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_5g1g(self, ctx, item1: GetAvatar, item2: GetAvatar):
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.five_guys_one_girl(), url=item1, url2=item2)
        await self.dag_embed(ctx, image, ctx.command.name)

    @commands.command(name="whyareyougay", aliases=["wayg"])
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_wayg(self, ctx, item1: GetAvatar, item2: GetAvatar):
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.why_are_you_gay(), url=item1, url2=item2)
        await self.dag_embed(ctx, image, ctx.command.name)

    @commands.command(name="obama")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_obama(self, ctx: AvimetryContext, *, item=None):
        meth = await self.do_dagpi(ctx, ImageFeatures.obama(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @commands.command(name="tweet")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_tweet(self, ctx, user: GetAvatar, username: str, *, text: str):
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.tweet(), text=text, url=user, username=username)
        await self.dag_embed(ctx, image, ctx.command.name)

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
            image = await self.bot.dagpi.image_process(
                ImageFeatures.youtube(), text=text, url=url,
                username=user.name if user_name is None else user_name)
        await self.dag_embed(ctx, image, ctx.command.name)

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
            image = await self.bot.dagpi.image_process(
                ImageFeatures.discord(), text=text, url=url,
                username=user.name if user_name is None else user_name)
        await self.dag_embed(ctx, image, ctx.command.name)

    @commands.command(name="captcha")
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def dag_captcha(self, ctx: AvimetryContext, text, *, item: GetAvatar):
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.captcha(), item, text=text)
        await self.dag_embed(ctx, image, ctx.command.name)

    @commands.command(brief="Convert emoji to url so you can download them")
    async def emojiurl(self, ctx: AvimetryContext, emoji):
        result = await emoji_to_url(emoji)
        await ctx.send(result)


def setup(bot):
    bot.add_cog(Image(bot))
