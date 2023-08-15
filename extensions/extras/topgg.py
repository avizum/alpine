"""
[Avimetry Bot]
Copyright (C) 2021 - 2023 avizum

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

import datetime
import random

import discord
from discord.ext import tasks
from topgg import ServerError
from topgg.types import BotVoteData

import core
from core import Bot


class TopGG(core.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.webhook = discord.Webhook.from_url(self.bot.settings["webhooks"]["vote_log"], session=self.bot.session)
        self.post.start()
        self.update.start()

    @tasks.loop(minutes=15)
    async def post(self):
        if self.bot.user.id != 756257170521063444:
            return
        try:
            await self.bot.topgg.post_guild_count(len(self.bot.guilds))
        except ServerError:
            pass
        headers = {"Authorization": self.bot.api["DBL"]}
        data = {
            "voice_connections": len(self.bot.voice_clients),
            "users": len(self.bot.users),
            "guilds": len(self.bot.guilds),
        }
        await self.bot.session.post(
            "https://discordbotlist.com/api/v1/bots/756257170521063444/stats",
            headers=headers,
            data=data,
        )

    @post.before_loop
    async def before_post(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5)
    async def update(self):
        if self.bot.user.id != 756257170521063444:
            return
        activities = [
            f"In {len(self.bot.guilds)} Servers",
            f"Looking at {len(self.bot.users)} Users",
            f"Made by @{self.bot.get_user(750135653638865017)}",
        ]
        await self.bot.change_presence(
            status=discord.Status.online, activity=discord.CustomActivity(name=f"@Avimetry | {random.choice(activities)}")
        )

    @update.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    @core.Cog.listener()
    async def on_dbl_vote(self, data: BotVoteData):
        if not isinstance(data, dict):
            return
        vote_type = "a bot list"
        user_id = None
        if isinstance(data.get("user"), dict):
            vote_type = "[Discord Boats](https://discord.boats/bot/756257170521063444/vote)"
            user_id = data.get("user").get("id")  # type: ignore # data should be there
        elif isinstance(data.get("user"), str):
            vote_type = "[Top.GG](https://top.gg/bot/756257170521063444/vote)"
            user_id = data.get("user")
        elif isinstance(data.get("id"), str):
            vote_type = "[Discord Bot List](https://discordbotlist.com/bots/avimetry/upvote)"
            user_id = data.get("id")
        if not user_id:
            return
        user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
        if not user:
            return
        user_embed = discord.Embed(title="Vote Recieved", description=f"Thank you for voting on {vote_type}!")
        await user.send(embed=user_embed)


async def setup(bot):
    await bot.add_cog(TopGG(bot))
