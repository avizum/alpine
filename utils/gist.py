"""
Posting and reading gists
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

from utils.avimetry import AvimetryBot
import aiohttp


class Gist:
    def __init__(self, bot: AvimetryBot, session: aiohttp.ClientSession):
        self.bot = bot
        self.session = session

    async def post(self, *, filename: str, description: str, content: str, public: bool = True):
        headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Avimetry-Gist-Cog',
                'Authorization': f'token {self.bot.settings["api_tokens"]["GitHub"]}'
        }

        data = {
            'public': public,
            'files': {
                filename: {
                    'content': content
                }
            },
            'description': description
        }
        output = await self.session.request("POST", "https://api.github.com/gists", json=data, headers=headers)
        info = await output.json()
        return info['html_url']
