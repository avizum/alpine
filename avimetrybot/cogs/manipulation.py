import discord
from discord.ext import commands
import aiozaneapi
from io import BytesIO
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



def setup(avimetry):
    avimetry.add_cog(manipulation(avimetry))