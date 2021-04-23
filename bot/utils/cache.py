from copy import deepcopy


class AvimetryCache:
    def __init__(self, avi):
        self.avi = avi
        self.guild_settings_cache = {}
        self.blacklisted_users = {}
        self.logging_cache = {}

    async def cache_all(self):
        await self.cache_guild_settings()
        await self.cache_blacklisted()
        await self.cache_logging()

    async def get_guild_prefixes(self, guild_id: int):
        prefix = self.guild_settings_cache.get(guild_id, None)
        return prefix["prefixes"]

    async def get_guild_settings(self, guild_id: int):
        return self.guild_settings_cache.get(guild_id, None)

    async def cache_new_guild(self, guild_id: int):
        try:
            await self.avi.pool.execute("INSERT INTO guild_settings VALUES ($1)", guild_id)
        except Exception:
            return
        self.guild_settings_cache[guild_id] = deepcopy({"prefixes": []})
        return self.guild_settings_cache[guild_id]

    async def cache_guild_settings(self):
        items = await self.avi.pool.fetch("SELECT * FROM guild_settings")
        for entry in items:
            self.guild_settings_cache[entry["guild_id"]] = {key: value for key, value in list(entry.items())}

    async def cache_blacklisted(self):
        items = await self.avi.pool.fetch("SELECT * FROM blacklist_user")
        for entry in items:
            self.blacklisted_users[entry["user_id"]] = entry["bl_reason"]

    async def cache_logging(self):
        items = await self.avi.pool.fetch("SELECT * FROM logging")
        for entry in items:
            self.logging_cache[entry["guild_id"]] = {key: value for key, value in list(entry.items())}
