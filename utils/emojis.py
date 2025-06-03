"""
[Alpine Bot]
Copyright (C) 2021 - 2024 avizum

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

__all__ = ("Emojis",)

from typing import ClassVar


class Emojis:
    BADGES: ClassVar[dict[str, str]] = {
        "hypesquad_balance": "<:hypesquad_balance:1308917879151788135>",
        "hypesquad_brilliance": "<:hypesquad_brilliance:1308917912869802085>",
        "hypesquad_bravery": "<:hypesquad_bravery:1308917891847946320>",
        "bug_hunter": "<:bug_hunter_level_one:965517882614218802>",
        "bug_hunter_level_2": "<:bug_hunter_level_two:965517899882192927>",
        "early_supporter": "<:early_supporter:965518847178309642>",
        "staff": "<:staff:1309297931894919168>",
        "partner": "<:partner:1309297922025852970>",
        "discord_certified_moderator": "<:certified_moderator:1309297911900803215>",
        "verified_bot": "<:verified_bot:1308918319860158555>",
        "verified_bot_developer": "<:verified_bot_developer:1309297945769807982>",
        "hypesquad": "<:hypesquad:1308917937998004275>",
        "bot_http_interactions": "<:bot:1011145603100725289>",
        "active_developer": "<:active_developer:1308917865172435016>",
        "guild_owner": "<:server_owner:1309623251919437966>",
    }

    STATUSES: ClassVar[dict[str, str]] = {
        "online": "<:status_online:810683593193029642>",
        "idle": "<:status_idle:810683571269664798>",
        "dnd": "<:status_dnd:810683560863989805>",
        "offline": "<:status_offline:810683581541515335>",
        "streaming": "<:status_streaming:810683604812169276>",
    }

    RED_TICK: ClassVar[str] = "<:redtick:777096756865269760>"
    GREEN_TICK: ClassVar[str] = "<:greentick:777096731438874634>"
    GRAY_TICK: ClassVar[str] = "<:graytick:791040199798030336>"
