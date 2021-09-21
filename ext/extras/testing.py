import discord
import core

from utils import AvimetryView


class SelectMenu(discord.ui.Select):
    def __init__(self, ctx, cogs: list[core.Cog]):
        self.cogs = cogs
        self.ctx = ctx
        opts = [
            discord.SelectOption(
                label=cog.qualified_name, description=cog.description
            )
            for cog in cogs
        ]

        super().__init__(placeholder="Select a category", options=opts)

    async def callback(self, interaction):
        await self.ctx.send_help(self.values[0])


class Test(core.Cog):

    @core.command()
    async def test(self, ctx):
        menu = AvimetryView(member=ctx.author)
        menu.add_item(SelectMenu(ctx, self.bot.cogs.values()))
        await ctx.send("Test/!??!?", view=menu)


def setup(bot):
    bot.add_cog(Test(bot))
