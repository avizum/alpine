"""
Posting and reading gists
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
import aiohttp

from typing import List


class GistFile:
    def __init__(self, *, filename: str, content: str) -> None:
        self.filename = filename
        self.content = content


class GistResponse:
    """
    Response of posting a gist.
    """

    def __init__(self, json: dict):
        self.json = json

    def to_response(self):
        self.url = self.json["url"]
        self.forks_url = self.json["forks_url"]
        self.commits_url = self.json["commits_url"]
        self.id = self.json["id"]
        self.node_id = self.json["node_id"]
        self.git_pull_url = self.json["git_pull_url"]
        self.git_push_url = self.json["git_push_url"]
        self.html_url = self.json["html_url"]
        self.files = self.json["files"]
        self.public = self.json["public"]
        self.created_at = self.json["created_at"]
        self.updated_at = self.json["updated_at"]
        self.description = self.json["description"]
        self.comments = self.json["comments"]
        self.user = self.json["user"]
        self.comments_url = self.json["comments_url"]
        self.owner = self.json["owner"]
        self.truncated = self.json["truncated"]
        return self


class HTTPException(Exception):
    pass


class GistClient:
    """
    Gist client that uses the GitHub Rest API.

    Parameters
    ----------
    token: :class:`str`
        The GitHub authorization token.
    session: :class:`aiohttp.ClientSession`
        The session used to connect to the API.
    """

    def __init__(self, token: str, session: aiohttp.ClientSession):
        self.token = token
        self.session = session
        self.url = "https://api.github.com/gists"

        self.session.headers["Accept"] = "application/vnd.github.v3+json"
        self.session.headers["User-Agent"] = "Avimetry-Gist-Cog"
        self.session.headers["Authorization"] = f"token {self.token}"

    async def post(
        self, *, description: str, files: List[GistFile], public: bool, raw: bool
    ):
        """
        Posts a gist.

        Parameters
        ----------
        description: :class:`str`
            The description of the gist.
        files: List[:class:`GistFile`]
            Required. List of :class:`GistFile` that make up the gist.
        public: :class:`bool`
            Indicate whether the gist is public.
        raw: :class:`bool`
            Whether to return raw json or the url of the gist.

        Returns
        -------
        URL: Union[:class:`str` :class:`dict`]
            The URL or the raw json of the newly created gist.
        """

        files = {f.filename: {"content": f.content} for f in files}

        data = {"public": public, "files": files, "description": description}
        output = await self.session.request("POST", self.url, json=data)
        json = await output.json()
        if raw:
            return json
        return json["html_url"]

    async def close(self):
        if not self.session.closed:
            await self.session.close()
