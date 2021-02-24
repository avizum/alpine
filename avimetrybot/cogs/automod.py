from discord.ext import commands
import re

regex_token = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}")


class AutoMod(commands.Cog, name="Auto Moderation"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avimetry.user:
            return

        if message.guild.id == 751490725555994716:
            if message.content.lower() == "bonk":
                guild = await self.avimetry.fetch_guild(760382234908688385)
                for i in guild.emojis:
                    if i.name == "bonk":
                        await message.add_reaction(i)
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
