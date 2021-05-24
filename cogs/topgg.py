"""
Cog for top.gg
Copyright (C) 2021 avizum

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

import discord

from utils import AvimetryBot
from discord.ext import commands, tasks


class TopGG(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi
        self.post.start()
        self.update.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != 839892190213439508:
            return
        try:
            user_voted = int(message.content)
        except Exception:
            return
        member = self.avi.get_user(user_voted)
        try:
            await member.send("Thank you for voting!")
        except discord.Forbidden:
            return

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        if data["type"] == "test":
            # this is roughly equivalent to
            # return await on_dbl_test(data) in this case
            return self.avi.dispatch('dbl_test', data)
        print(f"Received a vote:\n{data}")

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        """An event that is called whenever someone tests the webhook system for your bot on Top.gg."""
        print(f"Received a test vote:\n{data}")

    @tasks.loop(minutes=15)
    async def post(self):
        if self.avi.user.id != 756257170521063444:
            return
        await self.avi.topgg.post_guild_count(len(self.avi.guilds))

    @post.before_loop
    async def before_post(self):
        await self.avi.wait_until_ready()

    @tasks.loop(minutes=30)
    async def update(self):
        if self.avi.user.id != 756257170521063444:
            return
        status = discord.Status.online
        game = discord.Game(f"@Avimetry | {len(self.avi.guilds)} Servers")
        await self.avi.change_presence(status=status, activity=game)

    @update.before_loop
    async def before_update(self):
        await self.avi.wait_until_ready()


def setup(avi):
    avi.add_cog(TopGG(avi))
