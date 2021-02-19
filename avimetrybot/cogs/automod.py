from discord.ext import commands
import re

regex_token = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}")


class AutoMod(commands.Cog, name="auto moderation"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avimetry.user:
            return

        bot_token = [token for token in regex_token.findall(message.content)]
        if message.guild == 336642139381301249:
            return
        if bot_token:
            try:
                await message.delete()
            except Exception:
                return
            await message.channel.send(
                "I found tokens in your message and I deleted your message. Next time do not send your token here."
            )


def setup(avimetry):
    avimetry.add_cog(AutoMod(avimetry))
