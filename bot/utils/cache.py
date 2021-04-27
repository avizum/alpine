from copy import deepcopy
from discord.ext import tasks


class AvimetryCache:
    def __init__(self, avi):
        self.avi = avi
        self.cache_loop.start()

    @tasks.loop(hours=1)
    async def cache_loop(self):
        settings = await self.avi.pool.fetch("SELECT guild_id FROM guild_settings")
        settings_ids = [guild_id["guild_id"] for guild_id in settings]
        logging = await self.avi.pool.fetch("SELECT guild_id FROM logging")
        logging_ids = [guild_id["guild_id"] for guild_id in logging]
        for guild in self.avi.guilds:
            if guild.id not in settings_ids:
                print("settings")
                await self.avi.pool.execute("INSERT INTO guild_settings VALUES ($1)", guild.id)
                self.guild_settings_cache[guild.id] = deepcopy({"prefixes": []})
            if guild.id not in logging_ids:
                await self.avi.pool.execute("INSERT INTO logging VALUES ($1)", guild.id)
                self.logging_cache[guild.id] = {}

    @cache_loop.before_loop
    async def before_cache_loop(self):
        await self.avi.wait_until_ready()

    async def cache_all(self):
        self.guild_settings_cache = {}
        self.blacklist_cache = {}
        self.logging_cache = {}
        self.join_leave_cache = {}
        await self.cache_guild_settings()
        await self.cache_blacklisted()
        await self.cache_logging()
        await self.cache_join_leave()

    async def get_guild_prefixes(self, guild_id: int):
        prefix = self.guild_settings_cache.get(guild_id, None)
        print("lol")
        return prefix["prefixes"]

    async def get_guild_settings(self, guild_id: int):
        return self.guild_settings_cache.get(guild_id, None)

    async def add_to_cache(self, thing: dict, item):
        thing[item] = {}
        return thing[item]

    async def cache_new_guild(self, guild_id: int):
        try:
            await self.avi.pool.execute("INSERT INTO guild_settings VALUES ($1)", guild_id)
            await self.avi.pool.execute("INSERT INTO logging VALUES ($1)", guild_id)
        except Exception:
            return
        self.guild_settings_cache[guild_id] = deepcopy({"prefixes": []})
        self.logging_cache[guild_id] = {}
        return self.guild_settings_cache[guild_id]

    async def cache_guild_settings(self):
        items = await self.avi.pool.fetch("SELECT * FROM guild_settings")
        for entry in items:
            self.guild_settings_cache[entry["guild_id"]] = {key: value for key, value in list(entry.items())}

    async def cache_blacklisted(self):
        items = await self.avi.pool.fetch("SELECT * FROM blacklist_user")
        for entry in items:
            self.blacklist_cache[entry["user_id"]] = entry["bl_reason"]

    async def cache_logging(self):
        items = await self.avi.pool.fetch("SELECT * FROM logging")
        for entry in items:
            self.logging_cache[entry["guild_id"]] = {key: value for key, value in list(entry.items())}

    async def cache_join_leave(self):
        items = await self.avi.pool.fetch("SELECT * FROM join_leave")
        for entry in items:
            self.join_leave_cache[entry["guild_id"]] = {key: value for key, value in list(entry.items())}
