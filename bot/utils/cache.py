import discord
from copy import deepcopy


class AvimetryCache:
    def __init__(self, avi):
        self.avi = avi
        self.guild_settings = {}
        self.logging = {}
        self.join_leave = {}
        self.blacklist = {}

    async def get_guild_prefixes(self, guild_id: int):
        prefix = self.guild_settings.get(guild_id, None)
        print("lol")
        return prefix["prefixes"]

    async def get_guild_settings(self, guild_id: int):
        return self.guild_settings.get(guild_id, None)

    async def add_to_cache(self, thing: dict, guild_id: int):
        thing[guild_id] = {}
        await self.cache_all()

    async def cache_new_guild(self, guild_id: int):
        try:
            await self.avi.pool.execute("INSERT INTO guild_settings VALUES ($1)", guild_id)
        except Exception:
            return
        self.guild_settings[guild_id] = deepcopy({"prefixes": []})
        return self.guild_settings[guild_id]

    async def recache(self, guild: discord.Guild):
        guild_settings = await self.avi.pool.fetch("SELECT * FROM guild_settings WHERE guild_id = $1", guild.id)
        blacklist = await self.avi.pool.fetch("SELECT * FROM blacklist_user WHERE guild_id = $1", guild.id)
        logging = await self.avi.pool.fetch("SELECT * FROM logging WHERE guild_id = $1", guild.id)
        join_leave = await self.avi.pool.fetch("SELECT * FROM join_leave WHERE guild_id = $1", guild.id)

        for entry in guild_settings:
            settings = dict(entry)
            settings.pop("guild_id")
            self.guild_settings[entry["guild_id"]] = settings

        for entry in blacklist:
            self.blacklist[entry["user_id"]] = entry["bl_reason"]

        for entry in logging:
            logs = dict(entry)
            logs.pop("guild_id")
            self.logging[entry["guild_id"]] = logs

        for entry in join_leave:
            item = dict(entry)
            item.pop("guild_id")
            self.join_leave[entry["guild_id"]] = item

    async def cache_all(self):
        guild_settings = await self.avi.pool.fetch("SELECT * FROM guild_settings")
        blacklist = await self.avi.pool.fetch("SELECT * FROM blacklist_user")
        logging = await self.avi.pool.fetch("SELECT * FROM logging")
        join_leave = await self.avi.pool.fetch("SELECT * FROM join_leave")

        print("(Re)Caching...")
        for entry in guild_settings:
            settings = dict(entry)
            settings.pop("guild_id")
            self.guild_settings[entry["guild_id"]] = settings

        for entry in blacklist:
            self.blacklist[entry["user_id"]] = entry["bl_reason"]

        for entry in logging:
            logs = dict(entry)
            logs.pop("guild_id")
            self.logging[entry["guild_id"]] = logs

        for entry in join_leave:
            item = dict(entry)
            item.pop("guild_id")
            self.join_leave[entry["guild_id"]] = item

        print("(Re)Cached.")
