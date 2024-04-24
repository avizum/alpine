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


class MemberEmojiUrl(str):
    @classmethod
    async def convert(cls, ctx: Context, argument: str) -> str:
        try:
            item = await commands.MemberConverter().convert(ctx, argument)
            return item.display_avatar.replace(size=1024, format="png", static_format="png").url
        except commands.BadArgument:
            pass
        if EMOJI_REGEX.match(argument):
            item = await commands.EmojiConverter().convert(ctx, argument)
            return item.url
        if URL_REGEX.match(argument):
            return argument
        raise commands.BadArgument("Emoji or URL not found.")


def default(ctx: Context):
    return ctx.author.display_avatar.replace(size=1024, format="png", static_format="png").url


Author = commands.parameter(converter=MemberEmojiUrl, default=default, displayed_default="<your avatar>")


class Images(core.Cog):
    """
    Commands for image manipuation and more.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.emoji: str = "\U0001f4f7"
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)

    async def send_dagpi(self, ctx: Context, image: Image):
        embed = discord.Embed(
            title=ctx.command.name.title(),
            description=(
                f"Image processed in `{float(image.process_time) * 1000:.2f}ms`\n"
                "This command is powered by [Dagpi](https://dagpi.xyz)"
            ),
        )
        dag_image = discord.File(fp=image.image, filename=f"{ctx.command.name}.{image.format}")
        url = f"attachment://{dag_image.filename}"
        embed.set_image(url=url)
        await ctx.send(file=dag_image, embed=embed, no_edit=True)

    async def do_embed(self, ctx, file: discord.File):
        url = f"attachment://{file.filename}"
        embed.set_image(url=url)
        await ctx.send(file=file, embed=embed)

    @core.command(name="pixel")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_pixel(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a pixel effect to an image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.pixel(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="mirror")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_mirror(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Flips your image along the y axis.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.mirror(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="flip")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_flip(self, ctx: Context, item: MemberEmojiUrl = Author):
        """
        Flips an image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.flip(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="colors")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_colors(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Get the colors of an image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.colors(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="america")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_america(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds an American flag over the image
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.america(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="triggered")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_triggered(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a triggered filter over your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.triggered(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="expand")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_expand(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Animation that stretches your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.expand(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="wasted")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_wasted(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a wasted filter over your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.wasted(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="sketch")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_sketch(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        "Sketches" an image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.sketch(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="spin")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_spin(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a spinning effect to your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.spin(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="petpet")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_petpet(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Yes. Petpet.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.petpet(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="bonk")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_bonk(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Get bonked.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.bonk(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="bomb")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_bomb(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Boom. Explosion. On your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.bomb(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="dissolve")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_dissolve(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Dissolve effect from PowerPoint.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.dissolve(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="invert")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_invert(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Inverts an image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.invert(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="sobel")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_sobel(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a sobel filter over an image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.sobel(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="hog")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_hog(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Histogram of Oriented Gradients (HOG) for an image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.hog(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="triangle")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_triangle(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Cool effect on your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.triangle(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="blur")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_blur(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a blury effect to your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.blur(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="rgb")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_rgb(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Get a RGB graph of your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.rgb(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="angel")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_angel(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Puts your image on an angel. How nice.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.angel(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="satan")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_satan(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Puts your image on a demon. How bad.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.satan(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="delete")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_delete(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Puts your image on a delete dialog.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.delete(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="fedora")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_fedora(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Perry the platypus!
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.fedora(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="lego", disabled=True)
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_lego(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds lego filter on your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.lego(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="wanted")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_wanted(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Overlay your image on a wanted poster.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.wanted(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="stringify")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_stringify(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Turn your image to a ball of yarn.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.stringify(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="burn")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_burn(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Burn an image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.burn(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="freeze")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_freeze(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Ice on your image. Cold.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.freeze(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="earth")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_earth(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        The green and blue of the earth.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.earth(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="mosaic")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_mosaic(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a mosaic effect to your image
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.mosiac(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="sithlord")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_sithlord(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Are you a sith lord?
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.sith(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="shatter")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_shatter(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a glass break overlay to your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.shatter(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="jail")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_jail(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Overlays prison bars on your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.jail(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="pride")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_pride(self, ctx: Context, item: MemberEmojiUrl, flag: str):
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
        await self.send_dagpi(ctx, image)

    @core.command(name="trash")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_trash(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Throwing your image away.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.trash(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="deepfry")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_deepfry(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Deepfries your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.deepfry(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="ascii")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_ascii(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds an ascii effect to your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.ascii(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="charcoal")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_charcoal(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a charcoal effect you your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.charcoal(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="posterize")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_posterize(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Posterize your image
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.poster(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="sepia")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_sepia(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a sepia filter on to your photo.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.sepia(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="swirl")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_swirl(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Swirls your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.swirl(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="paint")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_paint(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Makes your image look like it was painted.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.paint(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="night")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_night(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Makes your photo darker so that it looks like it was taken at night.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.night(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="rainbow")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_rainbow(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Adds a rainbow filter to your image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.rainbow(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="magic", aliases=["magick", "magik"])
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_magic(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Distorts your image in a funny way.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.magik(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="5g1g")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_5g1g(self, ctx: Context, one: MemberEmojiUrl, two: MemberEmojiUrl):
        """
        Ya know, the five guys and one girl thing...
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.five_guys_one_girl(), url=one, url2=two)
            await self.send_dagpi(ctx, image)

    @core.command(name="whyareyougay", aliases=["wayg"])
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_wayg(self, ctx: Context, one: MemberEmojiUrl, two: MemberEmojiUrl):
        """
        Well why are you??
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.why_are_you_gay(), url=one, url2=two)
            await self.send_dagpi(ctx, image)

    @core.command(name="slap")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_slap(self, ctx: Context, one: MemberEmojiUrl, two: MemberEmojiUrl):
        """
        Slap someone.
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.slap(), url=one, url2=two)
            await self.send_dagpi(ctx, image)

    @core.command(name="obama")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_obama(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        You deseve an award. Here, award yourself.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.obama(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="bad")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_bad(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Bad image.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.bad(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="glitch")
    async def dag_glitch(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Add a glitch effect
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.glitch(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="polaroid")
    async def dag_polaroid(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Make your image look like a polaroid picture
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.polaroid(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="neon")
    async def dag_neon(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Neon effect
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.neon(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="comic")
    async def dag_comic(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Black and white comics
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.comic(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="cube")
    async def dag_cube(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Turns your image into a cube.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.cube(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="elmo")
    async def dag_elmo(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Burning elmo gif
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.elmo(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="album")
    async def dag_album(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        Make your image look like an album cover.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.album(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="rain")
    async def dag_rain(self, ctx: Context, *, item: MemberEmojiUrl = Author):
        """
        For rainy days.
        """
        async with ctx.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.rain(), item)
            await self.send_dagpi(ctx, image)

    @core.command(name="tweet")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_tweet(self, ctx, member: discord.Member = commands.Author, *, text: str):
        """
        Makes it look like you or someone else tweeted something.
        """
        url = member.display_avatar.replace(size=1024, format="png", static_format="png").url
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.tweet(), text=text, url=url, username=member.name)
            await self.send_dagpi(ctx, image)

    @core.command(name="youtube")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_youtube(self, ctx, member: discord.Member = commands.Author, *, text: str):
        """
        Generate a youtube comment.
        """
        url = member.display_avatar.replace(size=1024, format="png", static_format="png").url
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.youtube(), text=text, url=url, username=member.name)
            await self.send_dagpi(ctx, image)

    @core.command(name="discord")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_discord(self, ctx, user: discord.User = commands.Author, *, text: str):
        """
        Makes it look like someone said something.
        """
        url = str(user.display_avatar.replace(format="png", static_format="png", size=1024))
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.discord(), text=text, url=url, username=user.name)
            await self.send_dagpi(ctx, image)

    @core.command(name="captcha")
    @core.cooldown(2, 10, commands.BucketType.member)
    async def dag_captcha(self, ctx: Context, text, *, item: MemberEmojiUrl = Author):
        """
        Overlays your image on a captcha grid.
        """
        async with ctx.channel.typing():
            image = await self.bot.dagpi.image_process(ImageFeatures.captcha(), url=item, text=text)
        await self.send_dagpi(ctx, image)
