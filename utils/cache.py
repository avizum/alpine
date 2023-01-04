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

from __future__ import annotations

import logging

from copy import deepcopy
from typing import TYPE_CHECKING, TypedDict

from discord.ext import tasks

if TYPE_CHECKING:
    from core.avimetry import Bot


_log = logging.getLogger("avimetry")


class CacheUsers(TypedDict):
    timezone: str | None
    color: int | None
    dmed: bool


class CacheGuildSettings(TypedDict):
    prefixes: list[str]
    disabled_commands: list[str]
    disabled_channels: list[str]
    auto_unarchive: list[int]


class CacheVerification(TypedDict):
    role_id: int
    channel_id: int
    low: bool | None
    medium: bool | None
    high: bool | None

class CacheLogging(TypedDict):
    enabled: bool | None
    channel_id: int | None
    message_delete: bool | None
    message_edit: bool | None
    member_join: bool | None
    member_leave: bool | None
    member_ban: bool | None
    channel_edit: bool | None
    channel_delete: bool | None
    guild_edit: bool | None

class CacheJoinLeave(TypedDict):
    join_enabled: bool | None
    join_channel: int | None
    join_message: str | None
    leave_enabled: bool | None
    leave_channel: int | None
    leave_message: str | None

class Highlights(TypedDict):
    id: int
    triggers: list[str]
    blocked: list[int]


class Cache:
    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.cache_loop.start()
        self.guild_settings: dict[int, CacheGuildSettings | dict] = {}
        self.verification: dict[int, CacheVerification | dict] = {}
        self.logging: dict[int, CacheLogging | dict] = {}
        self.join_leave: dict[int, CacheJoinLeave | dict] = {}
        self.blacklist: dict[int, str] = {}
        self.users: dict[int, CacheUsers | dict] = {}
        self.highlights: dict[int, Highlights | dict] = {}

    @tasks.loop(minutes=5)
    async def cache_loop(self) -> None:
        await self.check_for_cache()

    @cache_loop.before_loop
    async def before_cache_loop(self) -> None:
        await self.bot.wait_until_ready()

    async def check_for_cache(self) -> None:
        cache_list = [
            self.guild_settings,
            self.verification,
            self.logging,
            self.join_leave,
        ]
        for guild in self.bot.guilds:
            for cache in cache_list:
                if guild.id not in cache:
                    cache[guild.id] = {}

    def __repr__(self) -> str:
        caches = [
            self.guild_settings,
            self.verification,
            self.logging,
            self.join_leave,
            self.blacklist,
            self.users,
        ]
        return f"<Cache size={sum(cache.__sizeof__() for cache in caches)}>"

    async def delete_all(self, gid: int) -> None:
        await self.bot.pool.execute("DELETE FROM guild_settings WHERE guild_id = $1", gid)
        try:
            self.guild_settings.pop(gid)
        except KeyError:
            return

    async def get_guild_settings(self, guild_id: int) -> CacheGuildSettings | dict | None:
        return self.guild_settings.get(guild_id)

    async def get_prefix(self, guild_id: int) -> list[str] | None:
        guild = self.guild_settings.get(guild_id)
        if not guild:
            return None
        return guild.get("prefixes")

    async def new_user(self, user_id: int) -> CacheUsers | dict | None:
        try:
            new = self.users[user_id]
        except KeyError:
            try:
                query = "INSERT INTO user_settings (user_id) VALUES ($1)"
                await self.bot.pool.execute(query, user_id)
            except Exception:
                pass
            new = self.users[user_id] = {}
        return new

    async def cache_new_guild(self, guild_id: int) -> dict[str, list]:
        try:
            await self.bot.pool.execute("INSERT INTO guild_settings VALUES ($1)", guild_id)
        except Exception:
            pass
        new = self.guild_settings[guild_id] = deepcopy(
            {
                "prefixes": [],
                "disabled_commands": [],
                "disabled_channels": [],
                "auto_unarchive": [],
            }
        )
        return new

    async def populate_cache(self) -> None:
        _log.info("Populating Cache...")

        guild_settings = await self.bot.pool.fetch("SELECT * FROM guild_settings")
        verification = await self.bot.pool.fetch("SELECT * FROM verification")
        logging = await self.bot.pool.fetch("SELECT * FROM logging")
        join_leave = await self.bot.pool.fetch("SELECT * FROM join_leave")
        users = await self.bot.pool.fetch("SELECT * FROM user_settings")
        blacklist = await self.bot.pool.fetch("SELECT * FROM blacklist")
        highlights = await self.bot.pool.fetch("SELECT * FROM highlights")

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

        for entry in highlights:
            item = dict(entry)
            item.pop("user_id")
            self.highlights[entry["user_id"]] = item

        _log.info("Cache Populated.")
