from discord.ext import commands


class TopGG(commands.Cog):
    def __init__(self, avi):
        self.avi = avi

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        """An event that is called whenever someone votes for the bot on Top.gg."""
        if data["type"] == "test":
            # this is roughly equivalent to
            # return await on_dbl_test(self, data) in this case
            return self.avi.dispatch('dbl_test', data)

        print(f"Received a vote:\n{data}")

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        """An event that is called whenever someone tests the webhook system for your bot on Top.gg."""
        print(f"Received a test vote:\n{data}")


def setup(avi):
    avi.add_cog(TopGG(avi))

