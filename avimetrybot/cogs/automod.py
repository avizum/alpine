from discord.ext import commands
import re

regex_token = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}")
regex_gamer_word = (
    r"(?P<main>(?:(?:(?<!s)[n\U0001F1F3]+(?:(?P<_nc>.)(?P=_nc)*)?[i1!|l\U0001f1ee]+(?:(?P<_ic>.)(?P=_ic)*)?\
    [g9\U0001F1EC](?:(?P<_gc>.)(?P=_gc)*)?)|(?:[k\U0001f1f0]+(?:(?P<_knc>.)(?P=_knc)*)?[n\U0001F1F3]+(?:\
    (?P<_nnc>.)(?P=_nnc)*)?[e3€£ÉÈëeÊêËéE\U0001f1ea]+(?:(?P<_enc>.)(?P=_enc)*)?[e3€£ÉÈëeÊêËéE\U0001f1ea]\
    +(?:(?P<_enc_>.)(?P=_enc_)*)?))[g9\U0001F1EC]+(?:(?P<_gc_>.)(?P=_gc_)*)?(?:[e3€£ÉÈëeÊêËéE\U0001f1ea]\
    +(?:(?P<_ec>.)(?P=_ec)*)?[r\U0001F1F7]+|(?P<soft>[a\U0001F1E6])))((?:(?P<_rc>.)(?P=_rc)*)?[s5]+)?(?!rd)"
)


class AutoMod(commands.Cog, name="Auto Moderation"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    @commands.Cog.listener()
    async def on_message(self, message):
        words = ["bday", "birthday", "birth date", "birth-day", "b-day", "birth-date"]
        if message.guild == 336642139381301249:
            return
        if message.author == self.avimetry.user:
            return
        if message.guild.id == 751490725555994716:
            if "bonk" in message.content.lower():
                guild = await self.avimetry.fetch_guild(760382234908688385)
                for i in guild.emojis:
                    if i.name == "bonk":
                        await message.add_reaction(i)
                        return
            for i in words:
                if i in message.content.lower():
                    await message.delete()
                    await message.channel.send("Do not say that.")

            bot_token = [token for token in regex_token.findall(message.content)]
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
