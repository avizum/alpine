"""
Handle bot cache for quick and easy access.
Copyright (C) 2021 - present avizum

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

from copy import deepcopy
from discord.ext import tasks


class AvimetryCache:
    def __init__(self, bot):
        self.bot = bot
        self.cache_loop.start()
        self.guild_settings = {}
        self.verification = {}
        self.logging = {}
        self.join_leave = {}
        self.blacklist = {}
        self.users = {}
        self.highlights = {}

    @tasks.loop(minutes=5)
    async def cache_loop(self):
        await self.check_for_cache()

    @cache_loop.before_loop
    async def before_cache_loop(self):
        await self.bot.wait_until_ready()

    async def check_for_cache(self):
        cache_list = [
            self.guild_settings,
            self.verification,
            self.logging,
            self.join_leave
        ]
        for guild in self.bot.guilds:
            for cache in cache_list:
                if guild.id not in cache:
                    cache[guild.id] = {}

    def __repr__(self):
        return "<AvimetryCache size=1000000000000000000000000000000000000000000000000000000000000000000000000000000000>"

    async def delete_all(self, gid):
        await self.bot.pool.execute("DELETE FROM guild_settings WHERE guild_id = $1", gid)
        try:
            self.guild_settings.pop(gid)
        except KeyError:
            return

    async def get_guild_settings(self, guild_id: int):
        return self.guild_settings.get(guild_id)

    async def get_prefix(self, guild_id: int):
        guild = self.guild_settings.get(guild_id)
        return guild.get('prefixes') if guild else None

    async def new_user(self, user_id: int):
        try:
            check = self.users[user_id]
            if check:
                return check
        except KeyError:
            try:
                query = "INSERT INTO user_settings (user_id) VALUES ($1)"
                await self.bot.pool.execute(query, user_id)
            except Exception:
                pass
            new = self.users[user_id] = {}
        return new

    async def cache_new_guild(self, guild_id: int):
        try:
            await self.bot.pool.execute("INSERT INTO guild_settings VALUES ($1)", guild_id)
        except Exception:
            pass
        new = self.guild_settings[guild_id] = deepcopy({"prefixes": []})
        return new

    async def cache_all(self):
        guild_settings = await self.bot.pool.fetch("SELECT * FROM guild_settings")
        verification = await self.bot.pool.fetch("SELECT * FROM verification")
        logging = await self.bot.pool.fetch("SELECT * FROM logging")
        join_leave = await self.bot.pool.fetch("SELECT * FROM join_leave")
        users = await self.bot.pool.fetch("SELECT * FROM user_settings")
        blacklist = await self.bot.pool.fetch("SELECT * FROM blacklist")

        print("(Re)Caching...")
        for entry in guild_settings:
            settings = dict(entry)
            settings.pop("guild_id")
            self.guild_settings[entry["guild_id"]] = settings

        for entry in verification:
            verify = dict(entry)
            verify.pop("guild_id")
            self.verification[entry["guild_id"]] = verify

        for entry in blacklist:
            self.blacklist[entry["user_id"]] = entry["reason"]

        for entry in users:
            user = dict(entry)
            user.pop("user_id")
            self.users[entry["user_id"]] = user

        for entry in logging:
            logs = dict(entry)
            logs.pop("guild_id")
            self.logging[entry["guild_id"]] = logs

        for entry in join_leave:
            item = dict(entry)
            item.pop("guild_id")
            self.join_leave[entry["guild_id"]] = item

        print("(Re)Cached.")
