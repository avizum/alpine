import discord
from discord.ext import commands
import aiozaneapi
import aiohttp
from io import BytesIO
import io
from PIL import Image

class manipulation(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry=avimetry

    @commands.command()
    async def deepfry(self, ctx, image=None):
        if image==None:
            image=str(ctx.author.avatar_url)
        try:
            result = await self.avimetry.zane.deepfry(image) 
        except aiozaneapi.GatewayError as err:
            print(f'Error has occurred on the server-side. {err}')
        except aiozaneapi.UnauthorizedError as err:
            print(f'Error has occurred on the client-side. {err}')
        
        with Image.open(BytesIO(result)) as my_image:
            # do whatever with your image
            output_buffer = BytesIO()
            my_image.save(output_buffer, "png") 
            output_buffer.seek(0)
        
            await ctx.send(file=discord.File(fp=output_buffer, filename="my_file.png"))
            await self.avimetry.zane.close()
            return await ctx.send(file=discord.File(io.BytesIO(magic.read()), filename="magic.gif"))

    @commands.command()
    async def floor(self, ctx, url=None):
        if url==None:
            url=ctx.author.avatar_url_as(format="png")
        else:
            try:
                member_url=await commands.MemberConverter().convert(ctx, url)
                url=member_url.avatar_url_as(format="png")
            except Exception:
                url=url
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as imgfloor:
                async with imgfloor.get(f"https://zane.ip-bash.com/api/floor?url={url}&token={self.avimetry.zanetoken}") as floor_result:
                    return await ctx.send(file=discord.File(io.BytesIO(await floor_result.read()), filename="floor.gif"))

    @commands.command()
    async def cube(self, ctx, url=None):
        if url==None:
            url=ctx.author.avatar_url_as(format="png")
        else:
            try:
                member_url=await commands.MemberConverter().convert(ctx, url)
                url=member_url.avatar_url_as(format="png")
            except Exception:
                url=url
        async with ctx.channel.typing():
            async with aiohttp.ClientSession() as imgcube:
                async with imgcube.get(f"https://zane.ip-bash.com/api/cube?url={url}&token={self.avimetry.zanetoken}") as cube_result:
                    return await ctx.send(file=discord.File(io.BytesIO(await cube_result.read()), filename="cube.png"))

            
def setup(avimetry):
    avimetry.add_cog(manipulation(avimetry))