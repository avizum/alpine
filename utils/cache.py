from copy import deepcopy
from discord.ext import tasks


class AvimetryCache:
    def __init__(self, avi):
        self.avi = avi
        self.cache_loop.start()
        self.guild_settings = {}
        self.verification = {}
        self.logging = {}
        self.join_leave = {}
        self.blacklist = {}
        self.users = {}

    @tasks.loop(minutes=5)
    async def cache_loop(self):
        await self.check_for_cache()

    @cache_loop.before_loop
    async def before_cache_loop(self):
        await self.avi.wait_until_ready()

    async def check_for_cache(self):
        cache_list = [
            self.guild_settings,
            self.verification,
            self.logging,
            self.join_leave
        ]
        for guild in self.avi.guilds:
            for cache in cache_list:
                if guild.id not in cache:
                    cache[guild.id] = {}

    async def delete_all(self, gid):
        await self.avi.pool.execute("DELETE FROM guild_settings WHERE guild_id = $1", gid)

    async def get_guild_settings(self, guild_id: int):
        return self.guild_settings.get(guild_id, None)

    async def new_user(self, user_id: int):
        try:
            check = self.users[user_id]
            if check:
                return check
        except KeyError:
            try:
                query = "INSERT INTO user_settings (user_id) VALUES ($1)"
                await self.avi.pool.execute(query, user_id)
            except Exception:
                pass
            new = self.users[user_id] = {}
        return new

    async def cache_new_guild(self, guild_id: int):
        try:
            await self.avi.pool.execute("INSERT INTO guild_settings VALUES ($1)", guild_id)
        except Exception:
            return
        self.guild_settings[guild_id] = deepcopy({"prefixes": []})
        return self.guild_settings[guild_id]

    async def cache_all(self):
        guild_settings = await self.avi.pool.fetch("SELECT * FROM guild_settings")
        verification = await self.avi.pool.fetch("SELECT * FROM verification")
        logging = await self.avi.pool.fetch("SELECT * FROM logging")
        join_leave = await self.avi.pool.fetch("SELECT * FROM join_leave")
        users = await self.avi.pool.fetch("SELECT * FROM user_settings")

        print("(Re)Caching...")
        for entry in guild_settings:
            settings = dict(entry)
            settings.pop("guild_id")
            self.guild_settings[entry["guild_id"]] = settings

        for entry in verification:
            verify = dict(entry)
            verify.pop("guild_id")
            self.verification[entry["guild_id"]] = verify

        for entry in users:
            check = dict(entry)
            if check["user_id"] and check["blacklist"]:
                self.blacklist[entry["user_id"]] = entry["blacklist"]

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
