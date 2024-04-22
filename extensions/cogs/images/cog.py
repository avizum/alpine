"""
[Alpine Bot]
Copyright (C) 2021 - 2024 avizum

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

import datetime as dt
from typing import TYPE_CHECKING

import discord
from asyncdagpi.image import Image
from asyncdagpi.image_features import ImageFeatures
from discord.ext import commands

import core
from core import Bot, Context
from utils.helpers import EMOJI_REGEX, URL_REGEX

if TYPE_CHECKING:
    from datetime import datetime


embed = discord.Embed()
args = discord.Member | discord.PartialEmoji | discord.Emoji | str | None


class GetAvatarOrImage(commands.Converter):
    async def convert(self, ctx: Context, argument: str | None = None) -> str | None:
        if argument is None:
            return ctx.author.display_avatar.replace(format="png", static_format="png", size=1024).url
        try:
            member = await commands.MemberConverter().convert(ctx, argument)
            return member.display_avatar.replace(format="png", static_format="png", size=1024).url
        except commands.MemberNotFound:
            if URL_REGEX.match(argument):
                return argument
            if EMOJI_REGEX.match(argument):
                emoji = await commands.EmojiConverter().convert(ctx, argument)
                return emoji.url
            return None


class Images(core.Cog):
    """
    Commands for image manipuation and more.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.emoji: str = "\U0001f4f7"
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)

    async def do_dagpi(self, ctx: Context, feature: ImageFeatures, argument, gif: bool = False):
        image = await GetAvatarOrImage().convert(ctx, argument)
        if image is None:
            if ctx.message.attachments:
                img = ctx.message.attachments[0]
                image = img.url
            else:
                image = str(ctx.author.display_avatar.replace(format="png", static_format="png", size=1024))
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(feature, image)
        return image

    async def dag_embed(self, ctx: Context, image: Image, title: str):
        embed = discord.Embed(
            title=title.title(),
            description=(
                f"Image processed in `{float(image.process_time) * 1000:.2f}ms`\n"
                "This command is powered by [Dagpi](https://dagpi.xyz)"
            ),
        )
        dag_image = discord.File(fp=image.image, filename=f"{title}.{image.format}")
        url = f"attachment://{dag_image.filename}"
        embed.set_image(url=url)
        await ctx.send(file=dag_image, embed=embed, no_edit=True)

    async def do_embed(self, ctx, file: discord.File):
        url = f"attachment://{file.filename}"
        embed.set_image(url=url)
        await ctx.send(file=file, embed=embed)

    @core.command(name="pixel")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_pixel(self, ctx: Context, *, item=None):
        """
        Adds a pixel effect to an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.pixel(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="mirror")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_mirror(self, ctx: Context, *, item=None):
        """
        Flips your image along the y axis.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.mirror(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="flip")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_flip(self, ctx: Context, item=None):
        """
        Flips an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.flip(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="colors")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_colors(self, ctx: Context, *, item=None):
        """
        Get the colors of an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.colors(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="america")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_america(self, ctx: Context, *, item=None):
        """
        Adds an American flag over the image
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.america(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="communism")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_communism(self, ctx: Context, *, item=None):
        """
        Adds a communism flag over an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.communism(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="triggered")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_triggered(self, ctx: Context, *, item=None):
        """
        Adds a triggered filter over your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.triggered(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="expand")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_expand(self, ctx: Context, *, item=None):
        """
        Animation that stretches your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.expand(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="wasted")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_wasted(self, ctx: Context, *, item=None):
        """
        Adds a wasted filter over your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.wasted(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="sketch")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_sketch(self, ctx: Context, *, item=None):
        """
        "Sketches" an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.sketch(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="spin")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_spin(self, ctx: Context, *, item=None):
        """
        Adds a spinning effect to your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.spin(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="petpet")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_petpet(self, ctx: Context, *, item=None):
        """
        Yes. Petpet.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.petpet(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="bonk")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_bonk(self, ctx: Context, *, item=None):
        """
        Get bonked.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.bonk(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="bomb")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_bomb(self, ctx: Context, *, item=None):
        """
        Boom. Explosion. On your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.bomb(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="dissolve")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_dissolve(self, ctx: Context, *, item=None):
        """
        Dissolve effect from PowerPoint.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.dissolve(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="shake", enabled=False)
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_shake(self, ctx: Context, *, item=None):
        """
        Shakes an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.shake(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="invert")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_invert(self, ctx: Context, *, item=None):
        """
        Inverts an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.invert(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="sobel")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_sobel(self, ctx: Context, *, item=None):
        """
        Adds a sobel filter over an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.sobel(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="hog")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_hog(self, ctx: Context, *, item=None):
        """
        Histogram of Oriented Gradients for an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.hog(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="triangle")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_triangle(self, ctx: Context, *, item=None):
        """
        Cool effect on your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.triangle(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="blur")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_blur(self, ctx: Context, *, item=None):
        """
        Adds a blury effect to your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.blur(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="rgb")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_rgb(self, ctx: Context, *, item=None):
        """
        Get a graph of colors.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.rgb(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="angel")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_angel(self, ctx: Context, *, item=None):
        """
        Puts your image on an angel. How nice.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.angel(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="satan")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_satan(self, ctx: Context, *, item=None):
        """
        Puts your image on a demon. How bad.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.satan(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="delete")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_delete(self, ctx: Context, *, item=None):
        """
        Puts your image on a delete dialog.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.delete(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="fedora")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_fedora(self, ctx: Context, *, item=None):
        """
        Perry the platypus!
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.fedora(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="hitler")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_hitler(self, ctx: Context, *, item=None):
        """
        Hmm, What's this?
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.hitler(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="lego", disabled=True)
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_lego(self, ctx: Context, *, item=None):
        """
        Adds lego filter on your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.lego(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="wanted")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_wanted(self, ctx: Context, *, item=None):
        """
        Overlay your image on a wanted poster.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.wanted(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="stringify")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_stringify(self, ctx: Context, *, item=None):
        """
        Turn your image to a ball of yarn.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.stringify(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="burn")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_burn(self, ctx: Context, *, item=None):
        """
        Burn an image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.burn(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="freeze")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_freeze(self, ctx: Context, *, item=None):
        """
        Ice on your image. Cold.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.freeze(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="earth")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_earth(self, ctx: Context, *, item=None):
        """
        The green and blue of the earth.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.earth(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="mosaic")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_mosaic(self, ctx: Context, *, item=None):
        """
        Adds a mosaic effect to your image
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.mosiac(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="sithlord")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_sithlord(self, ctx: Context, *, item=None):
        """
        Are you a sith lord?
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.sith(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="shatter")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_shatter(self, ctx: Context, *, item=None):
        """
        Adds a glass break overlay to your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.shatter(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="jail")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_jail(self, ctx: Context, *, item=None):
        """
        Overlays prison bars on your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.jail(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="pride")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_pride(self, ctx: Context, item: GetAvatarOrImage, flag: str):
        """
        Overlays a flag of choice on your image
        """
        flags = [
            "asexual",
            "bisexual",
            "gay",
            "genderfluid",
            "genderqueer",
            "intersex",
            "lesbian",
            "nonbinary",
            "progress",
            "pan",
            "trans",
        ]
        if flag.lower() not in flags:
            return await ctx.send(f"Your flag must be one of these:\n{', '.join(flags)}")
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.pride(), url=item, flag=flag)
        await self.dag_embed(ctx, image, ctx.command.name)

    @core.command(name="trash")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_trash(self, ctx: Context, *, item=None):
        """
        Throwing your image away.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.trash(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="deepfry")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_deepfry(self, ctx: Context, *, item=None):
        """
        Deepfries your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.deepfry(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="ascii")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_ascii(self, ctx: Context, *, item=None):
        """
        Adds an ascii effect to your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.ascii(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="charcoal")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_charcoal(self, ctx: Context, *, item=None):
        """
        Adds a charcoal effect you your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.charcoal(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="posterize")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_posterize(self, ctx: Context, *, item=None):
        """
        Posterize your image
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.poster(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="sepia")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_sepia(self, ctx: Context, *, item=None):
        """
        Adds a sepia filter on to your photo.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.sepia(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="swirl")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_swirl(self, ctx: Context, *, item=None):
        """
        Swirls your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.swirl(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="paint")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_paint(self, ctx: Context, *, item=None):
        """
        Makes your image look like it was painted.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.paint(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="night")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_night(self, ctx: Context, *, item=None):
        """
        Makes your photo darker so that it looks like it was taken at night.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.night(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="rainbow")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_rainbow(self, ctx: Context, *, item=None):
        """
        Adds a rainbow filter to your image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.rainbow(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="magic", aliases=["magick", "magik"])
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_magic(self, ctx: Context, *, item=None):
        """
        Distorts your image in a funny way.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.magik(), item)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="5g1g")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_5g1g(self, ctx, item1: GetAvatarOrImage, item2: GetAvatarOrImage):
        """
        Ya know, the five guys and one girl thing...
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.five_guys_one_girl(), url=item1, url2=item2)
        await self.dag_embed(ctx, image, ctx.command.name)

    @core.command(name="whyareyougay", aliases=["wayg"])
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_wayg(self, ctx, item1: GetAvatarOrImage, item2: GetAvatarOrImage):
        """
        Well why are you??
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.why_are_you_gay(), url=item1, url2=item2)
        await self.dag_embed(ctx, image, ctx.command.name)

    @core.command(name="slap")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_slap(self, ctx: Context, item1: GetAvatarOrImage, item2: GetAvatarOrImage):
        """
        Slap someone.
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.slap(), url=item1, url2=item2)

    @core.command(name="obama")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_obama(self, ctx: Context, *, item=None):
        """
        You deseve an award. Here award yourself.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.obama(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="bad")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_bad(self, ctx: Context, *, item=None):
        """
        Bad image.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.bad(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="glitch")
    async def dag_glitch(self, ctx: Context, *, item=None):
        """
        Add a glitch effect
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.glitch(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="polaroid")
    async def dag_polaroid(self, ctx: Context, *, item=None):
        """
        Make your image look like a polaroid picture
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.polaroid(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="neon")
    async def dag_neon(self, ctx: Context, *, item=None):
        """
        Neon effect
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.neon(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="comic")
    async def dag_comic(self, ctx: Context, *, item=None):
        """
        Black and white comics
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.comic(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="cube")
    async def dag_cube(self, ctx: Context, *, item=None):
        """
        Turns your image into a cube.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.cube(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="elmo")
    async def dag_elmo(self, ctx: Context, *, item=None):
        """
        Burning elmo gif
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.elmo(), item, True)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="album")
    async def dag_album(self, ctx: Context, *, item=None):
        """
        Make your image look like an album cover.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.album(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="rain")
    async def dag_rain(self, ctx: Context, *, item=None):
        """
        For rainy days.
        """
        meth = await self.do_dagpi(ctx, ImageFeatures.rain(), item, False)
        await self.dag_embed(ctx, meth, ctx.command.name)

    @core.command(name="tweet")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_tweet(self, ctx, user: GetAvatarOrImage, username: str, *, text: str):
        """
        Makes it look like you or someone else tweeted something.
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.tweet(), text=text, url=user, username=username)
        await self.dag_embed(ctx, image, ctx.command.name)

    @core.command(name="youtube")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_youtube(self, ctx, user: discord.Member, *, text: str | None = None):
        """
        Generate a youtube comment.
        """
        user_name = None
        if text is None:
            url = str(ctx.author.avatar.replace(format="png", static_format="png", size=1024))
            text = "I am an idiot for not putting the text in"
            user_name = ctx.author.name
        else:
            url = str(user.display_avatar.replace(format="png", static_format="png", size=1024))
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(
                ImageFeatures.youtube(),
                text=text,
                url=url,
                username=user.name if user_name is None else user_name,
            )
        await self.dag_embed(ctx, image, ctx.command.name)

    @core.command(name="discord")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_discord(self, ctx, user: discord.User | None = None, *, text: str | None = None):
        """
        Makes it look like someone said something.
        """
        user_name = None
        if text is None:
            url = str(ctx.author.avatar.replace(format="png", static_format="png", size=1024))
            text = "I am an idiot for not putting the text in"
            user_name = ctx.author.name
        else:
            url = str(user.display_avatar.replace(format="png", static_format="png", size=1024))
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(
                ImageFeatures.discord(),
                text=text,
                url=url,
                username=user.name if user_name is None else user_name,
            )
        await self.dag_embed(ctx, image, ctx.command.name)

    @core.command(name="captcha")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_captcha(self, ctx: Context, text, *, item: GetAvatarOrImage):
        """
        Overlays your image on a captcha grid.
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.captcha(), url=item, text=text)
        await self.dag_embed(ctx, image, ctx.command.name)

    @core.command(name="thoughtimage", aliases=["thinking"])
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_thought_image(self, ctx: Context, text, *, item: GetAvatarOrImage):
        """
        Overlays your image on a captcha grid.
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.thought_image(), url=item, text=text)
        await self.dag_embed(ctx, image, ctx.command.name)

    @core.command()
    async def emojiurl(self, ctx: Context, emoji):
        """
        Convert your emoji to a url.
        """
        result = await emoji_to_url(emoji)
        await ctx.send(result)
