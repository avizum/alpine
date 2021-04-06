import discord
from discord.ext import menus
from akinator.async_aki import Akinator


class AkinatorGame(menus.Menu):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.embed = None
        self.aki_client = Akinator()
        self.game = None

    async def send_initial_message(self, ctx, channel):
        self.game = await self.aki_client.start_game()
        self.embed = discord.Embed(
            title="Akinator",
            description=self.game
        )
        return await ctx.send(embed=self.embed)

    async def test(self, pee):
        while self.aki_client.progression <= 80:
            self.embed.description = self.game
            await self.message.edit(embed=self.embed)
            self.game = await self.aki_client.answer(pee)

    @menus.button("<:Yes:812133712967761951>")
    async def on_yes(self, _):
        await self.test("0")

    @menus.button("<:No:812133712946528316>")
    async def on_no(self, _):
        await self.test("1")

    @menus.button("<:IDontKnow:812133713046405230>")
    async def on_idontknow(self, _):
        await self.test("2")

    @menus.button("<:Probably:812133712962519100>")
    async def on_probably(self, _):
        await self.test("3")

    @menus.button("<:ProbablyNot:812133712665772113>")
    async def on_probablynot(self, _):
        await self.test("4")

    @menus.button("<:Back:815854941083664454>")
    async def on_back(self, _):
        await self.test("b")

    @menus.button("<:Stop:815859174667452426>")
    async def on_stop(self, _):
        self.embed.description = "stopped"
        await self.message.edit(embed=self.embed)
        self.stop()
