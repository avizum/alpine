"""
[Alpine Bot]
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
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import asyncpg
import discord

if TYPE_CHECKING:
    from core.alpine import Bot

__all__ = (
    "BaseData",
    "GuildData",
    "VerificationData",
    "LoggingData",
    "JoinLeaveData",
    "UserData",
    "HighlightsData",
    "BlacklistData",
    "Database",
)

_log = logging.getLogger("alpine")


class BaseData(ABC):
    def __repr__(self) -> str:
        name = self.__class__.__name__
        attrs = [name for name, value in self.__class__.__dict__.items() if isinstance(value, property)]
        fmt = ", ".join([f"{item}={getattr(self, item)}" for item in attrs])

        return f"{name}({fmt})"

    @abstractmethod
    async def insert(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self) -> None:
        raise NotImplementedError


class GuildData(BaseData):
    def __init__(self, guild_id: int, database: Database) -> None:
        self.guild_id: int = guild_id
        self.database: Database = database
        self._data: dict[str, Any] = {}

        self.database._guilds[guild_id] = self

    async def insert(self) -> GuildData:
        query = """
                INSERT INTO guild_settings (guild_id)
                VALUES ($1)
                ON CONFLICT (guild_id)
                DO UPDATE SET guild_id = $1
                RETURNING *
                """
        self.database._guilds[self.guild_id] = self
        self._data.update(await self.database.pool.fetchrow(query, self.guild_id))
        return self

    async def update(self, **kwargs: Any) -> GuildData:
        fmt = [f"{item} = ${number}" for number, item in enumerate(kwargs.keys(), start=2)]
        query = f"""
                UPDATE guild_settings
                SET {",".join(fmt)}
                WHERE guild_id = $1
                RETURNING *
                """
        self._data.update(await self.database.pool.fetchrow(query, self.guild_id, *kwargs.values()))
        return self

    async def delete(self) -> None:
        query = """
                DELETE FROM guild_settings
                WHERE guild_id = $1
                """
        del self.database._guilds[self.guild_id]
        await self.database.pool.execute(query, self.guild_id)

    @property
    def prefixes(self) -> list[str]:
        return self._data.get("prefixes", [])

    @property
    def disabled_commands(self) -> list[str]:
        return self._data.get("disabled_commands", [])

    @property
    def disabled_channels(self) -> list[int]:
        return self._data.get("disabled_channels", [])

    @property
    def auto_unarchive(self) -> list[int]:
        return self._data.get("auto_unarchive", [])

    @property
    def verification(self) -> VerificationData | None:
        return self.database._verification.get(self.guild_id)

    async def insert_verification(self) -> VerificationData:
        verification = VerificationData(self.guild_id, self.database)
        return await verification.insert()

    @property
    def logging(self) -> LoggingData | None:
        return self.database._logging.get(self.guild_id)

    async def insert_logging(self) -> LoggingData:
        logging = LoggingData(self.guild_id, self.database)
        return await logging.insert()

    @property
    def join_leave(self) -> JoinLeaveData | None:
        return self.database._join_leave.get(self.guild_id)

    async def insert_join_leave(self) -> JoinLeaveData:
        join_leave = JoinLeaveData(self.guild_id, self.database)
        return await join_leave.insert()


class VerificationData(BaseData):
    def __init__(self, guild_id: int, database: Database) -> None:
        self.guild_id: int = guild_id
        self.database: Database = database
        self._data: dict[str, Any] = {}

        self.database._verification[guild_id] = self

    async def insert(self) -> VerificationData:
        query = """
                INSERT INTO verification (guild_id)
                VALUES ($1)
                ON CONFLICT (guild_id)
                DO UPDATE SET guild_id = $1
                RETURNING *
                """
        self.database._verification[self.guild_id] = self
        self._data.update(await self.database.pool.fetchrow(query, self.guild_id))
        return self

    async def update(self, **kwargs: Any) -> VerificationData:
        fmt = [f"{item} = ${number}" for number, item in enumerate(kwargs.keys(), start=2)]
        query = f"""
                UPDATE verification
                SET {",".join(fmt)}
                WHERE guild_id = $1
                RETURNING *
                """
        self._data.update(await self.database.pool.fetchrow(query, self.guild_id, *kwargs.values()))
        return self

    async def delete(self) -> None:
        query = """
                DELETE FROM verification
                WHERE guild_id = $1
                """
        del self.database._verification[self.guild_id]
        await self.database.pool.execute(query)

    @property
    def role_id(self) -> int:
        return self._data.get("role_id", 0)

    @property
    def channel_id(self) -> int:
        return self._data.get("channel_id", 0)

    @property
    def low(self) -> bool:
        return self._data.get("low", False)

    @property
    def medium(self) -> bool:
        return self._data.get("medium", False)

    @property
    def high(self) -> bool:
        return self._data.get("high", False)


class LoggingData(BaseData):
    def __init__(self, guild_id: int, database: Database) -> None:
        self.guild_id: int = guild_id
        self.database: Database = database
        self._data: dict[str, Any] = {}
        self._webhook: discord.Webhook | None = None

        self.database._logging[guild_id] = self

    async def insert(self) -> LoggingData:
        query = """
                INSERT INTO logging (guild_id)
                VALUES ($1)
                ON CONFLICT (guild_id)
                DO UPDATE SET guild_id = $1
                RETURNING *
                """
        self.database._logging[self.guild_id] = self
        self._data.update(await self.database.pool.fetchrow(query, self.guild_id))
        return self

    async def update(self, **kwargs: Any):
        fmt = [f"{item} = ${number}" for number, item in enumerate(kwargs.keys(), start=2)]
        query = f"""
                UPDATE logging
                SET {",".join(fmt)}
                WHERE guild_id = $1
                RETURNING *
                """
        self._data.update(await self.database.pool.fetchrow(query, self.guild_id, *kwargs.values()))

    async def delete(self) -> None:
        query = """
                DELETE FROM logging
                WHERE guild_id = $1
                """
        del self.database._logging[self.guild_id]
        await self.database.pool.execute(query)

    @property
    def enabled(self) -> bool:
        return self._data.get("enabled", False)

    @property
    def webhook_url(self) -> str | None:
        return self._data.get("webhook")

    @property
    def webhook(self) -> discord.Webhook | None:
        url: str | None = self._data.get("webhook")

        if not url:
            return None
        elif self._webhook and self._webhook.url == url:
            return self._webhook

        webhook = discord.Webhook.from_url(url, client=self.database.bot)
        self._webhook = webhook
        return webhook

    @property
    def message_delete(self) -> bool:
        return self._data.get("message_delete", False)

    @property
    def message_edit(self) -> bool:
        return self._data.get("message_edit", False)

    @property
    def member_join(self) -> bool:
        return self._data.get("member_join", False)

    @property
    def member_leave(self) -> bool:
        return self._data.get("member_leave", False)

    @property
    def member_ban(self) -> bool:
        return self._data.get("member_ban", False)

    @property
    def channel_edit(self) -> bool:
        return self._data.get("channel_edit", False)

    @property
    def channel_delete(self) -> bool:
        return self._data.get("channel_delete", False)

    @property
    def guild_edit(self) -> bool:
        return self._data.get("guild_edit", False)


class JoinLeaveData(BaseData):
    def __init__(self, guild_id: int, database: Database) -> None:
        self.guild_id: int = guild_id
        self.database: Database = database
        self._data: dict[str, Any] = {}

        self.database._join_leave[guild_id] = self

    async def insert(self) -> JoinLeaveData:
        query = """
                INSERT INTO join_leave (guild_id)
                VALUES ($1)
                ON CONFLICT (guild_id)
                DO UPDATE SET guild_id = $1
                RETURNING *
                """
        self.database._join_leave[self.guild_id] = self
        self._data.update(await self.database.pool.fetchrow(query, self.guild_id))
        return self

    async def update(self, **kwargs: Any):
        fmt = [f"{item} = ${number}" for number, item in enumerate(kwargs.keys(), start=2)]
        query = f"""
                UPDATE join_leave
                SET {",".join(fmt)}
                WHERE guild_id = $1
                RETURNING *
                """
        self._data.update(await self.database.pool.fetchrow(query, self.guild_id, *kwargs.values()))

    async def delete(self) -> None:
        query = """
                DELETE FROM join_leave
                WHERE guild_id = $1
                """
        del self.database._join_leave[self.guild_id]
        await self.database.pool.execute(query)

    @property
    def enabled(self) -> bool:
        return self._data.get("enabled", False)

    @property
    def channel_id(self) -> int:
        return self._data.get("channel_id", 0)

    @property
    def join_message(self) -> str | None:
        return self._data.get("join_message")

    @property
    def leave_message(self) -> str | None:
        return self._data.get("leave_message")


class UserData(BaseData):
    def __init__(self, user_id: int, database: Database) -> None:
        self.user_id: int = user_id
        self.database: Database = database
        self._data: dict[str, Any] = {}

        self.database._users[user_id] = self

    async def insert(self) -> UserData:
        query = """
                INSERT INTO user_settings (user_id)
                VALUES ($1)
                ON CONFLICT (user_id)
                DO UPDATE SET user_id = $1
                RETURNING *
                """
        self.database._users[self.user_id] = self
        self._data.update(await self.database.pool.fetchrow(query, self.user_id))
        return self

    async def update(self, **kwargs: Any) -> UserData:
        fmt = [f"{item} = ${number}" for number, item in enumerate(kwargs.keys(), start=2)]
        query = f"""
                UPDATE user_settings
                SET {",".join(fmt)}
                WHERE user_id = $1
                RETURNING *
                """
        self._data.update(await self.database.pool.fetchrow(query, self.user_id, *kwargs.values()))
        return self

    async def delete(self) -> None:
        query = """
                DELETE FROM user_settings
                WHERE user_id = $1
                """
        del self.database._users[self.user_id]
        await self.database.pool.execute(query)

    @property
    def timezone(self) -> str | None:
        return self._data.get("timezone")

    @property
    def color(self) -> int:
        return self._data.get("color", 0)

    @property
    def dmed(self) -> bool:
        return self._data.get("dmed", False)


class HighlightsData(BaseData):
    def __init__(self, user_id: int, database: Database) -> None:
        self.user_id: int = user_id
        self.database: Database = database
        self._data: dict[str, Any] = {}

        self.database._highlights[user_id] = self

    async def insert(self) -> HighlightsData:
        query = """
                INSERT INTO highlights (user_id)
                VALUES ($1)
                ON CONFLICT (user_id)
                DO UPDATE SET user_id = $1
                RETURNING *
                """
        self.database._highlights[self.user_id] = self
        self._data.update(await self.database.pool.fetchrow(query, self.user_id))
        return self

    async def update(self, **kwargs: Any) -> HighlightsData:
        fmt = [f"{item} = ${number}" for number, item in enumerate(kwargs.keys(), start=2)]
        query = f"""
                UPDATE highlights
                SET {",".join(fmt)}
                WHERE user_id = $1
                RETURNING *
                """
        self._data.update(await self.database.pool.fetchrow(query, self.user_id, *kwargs.values()))
        return self

    async def delete(self) -> None:
        query = """
                DELETE FROM highlights
                WHERE user_id = $1
                """
        del self.database._highlights[self.user_id]
        await self.database.pool.execute(query)

    @property
    def triggers(self) -> list[str]:
        return self._data.get("triggers", [])

    @property
    def blocked(self) -> list[int]:
        return self._data.get("blocked", [])


class BlacklistData(BaseData):
    def __init__(self, user_id: int, database: Database) -> None:
        self.user_id: int = user_id
        self.database: Database = database
        self._data: dict[str, Any] = {}

        self.database._blacklists[user_id] = self

    async def insert(self, reason: str) -> BlacklistData:
        query = """
                INSERT INTO blacklist (user_id, reason)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET user_id = $1
                RETURNING *
                """
        self.database._blacklists[self.user_id] = self
        self._data.update(await self.database.pool.fetchrow(query, self.user_id, reason))
        return self

    async def update(self, reason: str) -> None:
        query = """
                UPDATE blacklist
                SET reason = $2
                WHERE user_id = $1
                RETURNING *
                """
        self._data.update(await self.database.pool.fetchrow(query, self.user_id, reason))

    async def delete(self) -> None:
        query = """
                DELETE FROM blacklist
                WHERE user_id = $1
                """
        del self.database._blacklists[self.user_id]
        await self.database.pool.execute(query, self.user_id)

    @property
    def reason(self) -> str:
        return self._data["reason"]


class Database:
    """
    Manages asyncpg Pool and the Cache.
    """

    pool: asyncpg.Pool

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self._guilds: dict[int, GuildData] = {}
        self._verification: dict[int, VerificationData] = {}
        self._logging: dict[int, LoggingData] = {}
        self._join_leave: dict[int, JoinLeaveData] = {}
        self._blacklists: dict[int, BlacklistData] = {}
        self._users: dict[int, UserData] = {}
        self._highlights: dict[int, HighlightsData] = {}
        self.bot.loop.create_task(self.__initialize())

    def __repr__(self) -> str:
        caches = [
            self._guilds,
            self._verification,
            self._logging,
            self._join_leave,
            self._blacklists,
            self._users,
            self._highlights,
        ]
        return f"<Database cache_size={sum(cache.__sizeof__() for cache in caches)}>"

    async def __initialize(self) -> None:
        self.pool = await asyncpg.create_pool(**self.bot.settings["postgresql"])  # type: ignore
        await self.__populate_cache()

    async def __populate_cache(self) -> None:
        guilds = await self.pool.fetch("SELECT * FROM guild_settings")
        verification = await self.pool.fetch("SELECT * FROM verification")
        logging = await self.pool.fetch("SELECT * FROM logging")
        join_leave = await self.pool.fetch("SELECT * FROM join_leave")
        users = await self.pool.fetch("SELECT * FROM user_settings")
        blacklists = await self.pool.fetch("SELECT * FROM blacklist")
        highlights = await self.pool.fetch("SELECT * FROM highlights")
        _log.info("Fetched data.")

        for guild_data in guilds:
            guild = GuildData(guild_data["guild_id"], self)
            guild._data.update(guild_data)

        for verification_data in verification:
            verification = VerificationData(verification_data["guild_id"], self)
            verification._data.update(verification_data)

        for logging_data in logging:
            logging = LoggingData(logging_data["guild_id"], self)
            logging._data.update(logging_data)

        for join_leave_data in join_leave:
            join_leave = JoinLeaveData(join_leave_data["guild_id"], self)
            join_leave._data.update(join_leave_data)

        for user_data in users:
            user = UserData(user_data["user_id"], self)
            user._data.update(user_data)

        for blacklist_data in blacklists:
            blacklist = BlacklistData(blacklist_data["user_id"], self)
            blacklist._data.update(blacklist_data)

        for highlight_data in highlights:
            highlight = HighlightsData(highlight_data["user_id"], self)
            highlight._data.update(highlight_data)

        _log.info("Cached data.")

    def get_guild(self, guild_id: int) -> GuildData | None:
        return self._guilds.get(guild_id)

    def get_user(self, user_id: int) -> UserData | None:
        return self._users.get(user_id)

    def get_highlights(self, user_id: int) -> HighlightsData | None:
        return self._highlights.get(user_id)

    def get_blacklist(self, user_id: int) -> BlacklistData | None:
        return self._blacklists.get(user_id)

    async def fetch_guild(self, guild_id: int) -> GuildData:
        guild = GuildData(guild_id, self)
        return await guild.insert()

    async def fetch_user(self, user_id: int) -> UserData:
        user = UserData(user_id, self)
        return await user.insert()

    async def fetch_highlights(self, user_id: int) -> HighlightsData:
        highlights = HighlightsData(user_id, self)
        return await highlights.insert()

    async def blacklist(self, user_id: int, /, *, reason: str) -> BlacklistData:
        blacklist = BlacklistData(user_id, self)
        return await blacklist.insert(reason)

    async def get_or_fetch_guild(self, guild_id: int) -> GuildData:
        return self.get_guild(guild_id) or await self.fetch_guild(guild_id)

    async def get_or_fetch_user(self, user_id: int) -> UserData:
        return self.get_user(user_id) or await self.fetch_user(user_id)
