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

from __future__ import annotations

import datetime as dt
import inspect
import os
import pathlib
from typing import TYPE_CHECKING

import discord
import humanize
import psutil
from discord import app_commands
from discord.ext import commands
from topgg import NotFound, ServerError

import core
from utils import Timer

if TYPE_CHECKING:
    from datetime import datetime

    from core import Bot, Context


class BotInfo(core.Cog, name="Bot Info"):
    """
    Bot Information commands
    """

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.emoji: str = "\U00002139"
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)
        self.process: psutil.Process = psutil.Process(os.getpid())
        self.request_wh: discord.Webhook = discord.Webhook.from_url(
            self.bot.settings["webhooks"]["request_log"], session=self.bot.session
        )

    @core.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        ctx: Context = await self.bot.get_context(message)
        if message.author == self.bot.user:
            return
        if message.content in [
            f"<@{self.bot.user.id}>",
            f"<@!{self.bot.user.id}>",
        ]:
            if not ctx.bot_permissions.send_messages:
                return
            command = self.bot.get_command("prefix")
            if command is None:
                return
            ctx.command = command
            await command(ctx)

        if message.guild and not message.guild.chunked:
            await message.guild.chunk()

    @core.command()
    async def news(self, ctx: Context):
        """
        Show the bot's news.
        """
        embed = discord.Embed(title="\U0001f4f0 Alpine News", description=self.bot.news)
        await ctx.send(embed=embed)

    @core.command()
    async def about(self, ctx: Context):
        """
        Show some information about Alpine.
        """
        embed = discord.Embed(title="Info about Alpine")
        embed.add_field(name="Latest News", value=self.bot.news, inline=False)
        async with ctx.channel.typing():
            async with self.bot.session.get("https://api.github.com/repos/avizum/alpine/commits") as resp:
                items = await resp.json()
        try:
            commits = "\n".join(f"[`{cm['sha'][:7]}`]({cm['html_url']}) {cm['commit']['message']}" for cm in items[:3])
        except KeyError:
            commits = "Could not get commits."
        embed.add_field(name="Latest Commits", value=commits, inline=False)
        delta_uptime = dt.datetime.now(dt.timezone.utc) - self.bot.launch_time
        embed.add_field(
            name="Info",
            value=f"Up for {humanize.precisedelta(delta_uptime)},\n`{round(self.bot.latency*1000)}ms` latency",
        )
        embed.add_field(
            name="Stats",
            value=f"{len(self.bot.guilds)} Servers\n{len(self.bot.users)} Users",
        )
        embed.set_thumbnail(url=ctx.me.display_avatar.url)
        owner = self.bot.get_user(750135653638865017)
        if owner is not None:
            embed.set_footer(text=f"Made by {owner} :)", icon_url=owner.display_avatar.url)
        await ctx.send(embed=embed)

    @core.command(name="credits")
    async def alpine_credits(self, ctx: Context):
        """
        List of people that have contributed to Alpine.

        If you want to contribute, Check out the GitHub repo.
        """
        # fmt: off
        credit_list = [
            (750135653638865017, "Bot Developer", "https://github.com/avizum",),
            (547280209284562944, "Bot Testing", "https://github.com/LereUwU",),
            (672122220566413312, "Original Avatar Design", "discord://-/users/672122220566413312",),
            (80088516616269824, "discord.py Developer", "https://github.com/Rapptz",),
            (171539705043615744, "Error Tracking Idea", "https://github.com/iDutchy",),
            (733370212199694467, "Contributor", "https://github.com/MrArkon/",),
        ]
        # fmt: on

        embed = discord.Embed(
            title="Credits",
            description="\n".join(f"[{self.bot.get_user(user)}]({credit}): {role}" for user, role, credit in credit_list),
        )

        await ctx.send(embed=embed)

    @core.command(aliases=["github"])
    async def commits(self, ctx: Context):
        """
        Gets the recent commits in the Alpine repo.

        This shows the recent commits on the repo.
        You can contribute on the repo.
        """
        async with ctx.channel.typing():
            async with self.bot.session.get("https://api.github.com/repos/avizum/alpine/commits") as resp:
                items = await resp.json()
        try:
            commit_list = [f"[`{cm['sha'][:7]}`]({cm['html_url']}) {cm['commit']['message']}" for cm in items[:10]]
        except KeyError:
            return await ctx.send("An error occured while trying to get the commits. Try again later.")
        embed = discord.Embed(title="Recent commits", description="\n".join(commit_list))
        embed.set_footer(text="Contribute to Alpine by doing magic.")
        await ctx.send(embed=embed)

    @core.command()
    async def uptime(self, ctx: Context):
        """
        Check how long the bot has been up for.
        """
        delta_uptime = dt.datetime.now(dt.timezone.utc) - self.bot.launch_time
        ue = discord.Embed(
            title="Current Uptime",
            description=humanize.precisedelta(delta_uptime, format="%.2g"),
        )
        await ctx.send(embed=ue)

    @core.command(hybrid=True)
    async def ping(self, ctx: Context):
        """
        Check the bot's latencies.

        Websocket: latency between the bot and Discord's servers.
        Typing: how long it takes to send typing to the channel.
        Database: how long it takes to query the database.
        """
        async with Timer() as api:
            await ctx.channel.typing()
        async with Timer() as db:
            await self.bot.database.pool.execute("SELECT 1")
        ping_embed = discord.Embed(title="Pong!")
        ping_embed.add_field(
            name="<:avimetry:1020851768143380522> Websocket Latency",
            value=f"`{self.bot.latency * 1000:,.2f} ms`",
            inline=False,
        )
        ping_embed.add_field(
            name="<a:typing:877445218729861190> Typing Latency",
            value=f"`{api.total_time * 1000:,.2f} ms`",
            inline=False,
        )
        ping_embed.add_field(
            name="<:pgsql:877445172093403166> Database Latency",
            value=f"`{db.total_time * 1000:,.2f} ms`",
            inline=False,
        )
        await ctx.message.add_reaction("<:greentick:777096731438874634>")
        await ctx.send(embed=ping_embed)

    @core.command()
    async def hello(self, ctx: Context):
        """
        Shows the message that is sent when I join a server.
        """
        embed = discord.Embed(
            title="\U0001f44b Hey, I am Alpine!",
            description=f"Hello {ctx.author.mention}, I am a bot made by [avizum.](https://github.com/avizum)",
            color=0x5E9BBF,
        )
        embed.add_field(name=f"{ctx.clean_prefix}help", value="Sends the help page.", inline=False)
        embed.add_field(
            name=f"{ctx.clean_prefix}settings",
            value="Manage Alpine's settings for this server.",
            inline=False,
        )
        embed.set_footer(text="This message can be deleted.")
        await ctx.send(embed=embed)

    @core.command()
    async def invite(self, ctx: Context, permissions: int = 8):
        """
        Invite me to your server.
        """
        perm = discord.Permissions(permissions)
        view = discord.ui.View(timeout=None)
        invite_embed = discord.Embed(
            title="Alpine Invite",
            description="Invite me to your server! Here are the invite links.",
        )
        invite_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                url=discord.utils.oauth_url(self.bot.user.id, permissions=perm),
                label="Invite with slash-commands",
            )
        )
        view.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                url=self.bot.support,
                label="Support server",
            )
        )
        await ctx.send(embed=invite_embed, view=view)

    @core.command()
    async def invitebot(self, ctx: Context, bot: discord.Member | discord.User, permissions: int = 8):
        """
        Get the invite link for a Bot.

        If you mention a bot, I will try to find their Top.GG page and send it. If I can't find it, then
        I will generate an invite link and send it.
        """
        perm = discord.Permissions(permissions)
        view = discord.ui.View(timeout=None)
        if bot.bot:
            invite_embed = discord.Embed(title=f"{bot.name} Invite")
            invite_embed.set_thumbnail(url=bot.display_avatar.url)
            try:
                top = await self.bot.topgg.get_bot_info(bot.id)
                invite_embed.description = f"Invite {bot.name} to your server! Here is the invite link."
                link = f"https://top.gg/bot/{bot.id}"
                view.add_item(
                    discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label=f"{bot.name} (top.gg)",
                        url=link,
                    )
                )
                view.add_item(
                    discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label=f"{bot.name}'s support server",
                        url=f"https://discord.gg/{top.support}",
                    )
                )
            except (NotFound, ServerError):
                invite_embed.description = f"Invite {bot.name} to your server! Here is the invite link."
                link = discord.utils.oauth_url(bot.id, permissions=perm)
                view.add_item(
                    discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label=f"{bot.name} Invite",
                        url=discord.utils.oauth_url(bot.id, permissions=perm),
                    )
                )
            await ctx.send(embed=invite_embed, view=view)
        else:
            await ctx.send("That is not a bot.")

    @core.command(aliases=["lc", "linec", "lcount"])
    async def linecount(self, ctx: Context):
        """
        Check how many lines of code the bot has.
        """
        path = pathlib.Path("./")
        comments = coros = funcs = classes = lines = imports = files = char = 0
        for item in path.rglob("*.py"):
            venv = os.environ["VIRTUAL_ENV"]
            if venv and str(item).startswith(venv.split("/")[-1]):
                continue
            else:
                files += 1
                with item.open() as of:
                    for line in of.readlines():
                        line = line.strip()
                        if line.startswith("class"):
                            classes += 1
                        if line.startswith("def"):
                            funcs += 1
                        if line.startswith("async def"):
                            coros += 1
                        if "import" in line:
                            imports += 1
                        if "#" in line:
                            comments += 1
                        lines += 1
                        char += len(line)
        embed = discord.Embed(
            title="Line Count",
            description=(
                "```py\n"
                f"Files: {files:,}\n"
                f"Imports: {imports:,}\n"
                f"Characters: {char:,}\n"
                f"Lines: {lines:,}\n"
                f"Classes: {classes:,}\n"
                f"Functions: {funcs:,}\n"
                f"Coroutines: {coros:,}\n"
                f"Comments: {comments:,}"
                "```"
            ),
        )
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(url=self.bot.source, label="Source"))
        await ctx.send(embed=embed, view=view)

    @core.command()
    @core.cooldown(1, 300, commands.BucketType.user)
    async def request(self, ctx: Context, *, request):
        """
        Request a feature to be added to Alpine.

        Spamming this command or sending spam requests will get you blacklisted from the bot.
        """
        conf = await ctx.confirm(message=f"Are sure you want to send this request?\n> {request}")
        if conf.result:
            req_send = discord.Embed(title=f"Request from {ctx.author}", description=f"```{request}```")

            await self.request_wh.send(embed=req_send)
            req_embed = discord.Embed(
                title="Request sent",
                description=(
                    "Thank you for your request! It has been sent to the support server. "
                    "Spam will get you permanently blacklisted from Alpine."
                ),
            )
            req_embed.add_field(name="Your request", value=f"```{request}```")
            return await ctx.send(embed=req_embed)
        return await conf.message.edit(content="Okay, I will not send it.")

    @core.command()
    async def support(self, ctx: Context):
        """
        Send the bot's support server link.
        """
        await ctx.send(self.bot.support)

    @core.command(hybrid=True)
    async def vote(self, ctx: Context):
        """
        Support Alpine by voting!
        """
        view = discord.ui.View()
        links = [
            ("Top.gg", "https://top.gg/bot/756257170521063444/vote"),
            ("Discord Bot List", "https://discordbotlist.com/bots/avimetry/upvote"),
        ]
        for name, link in links:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=name, url=link))
        vote_embed = discord.Embed(
            title="Vote for Alpine",
            description="Thank you for voting for me!\nYour support is greatly appreciated :)",
        )
        vote_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=vote_embed, view=view)

    # If you run an instance of this bot, Please do not remove this command.
    # - avizum
    @core.command(hybrid=True)
    async def source(self, ctx: Context, *, command: str | None = None):
        """
        Send the bot's source or a source of a command.

        Typing a command will send the source of a command instead.
        """
        button = discord.ui.Button
        view = discord.ui.View(timeout=None)
        source_embed = discord.Embed(
            title="Alpine's source",
            timestamp=dt.datetime.now(dt.timezone.utc),
        )
        git_link = f"{self.bot.source}/blob/master/"
        license_link = f"{self.bot.source}/blob/master/LICENSE"
        if not command:
            if self.bot.user.id != 756257170521063444:
                source_embed.description = (
                    "This bot is an instance of Alpine.\n"
                    "Click below for the source."
                    "Made by avizum\n"
                    "Follow the license"
                )
            else:
                source_embed.description = (
                    "Click below for the source of Alpine.\n" "I am made by avizum\n" "Follow the license and please star :)"
                )
            view.add_item(button(style=discord.ButtonStyle.link, label="Source", url=self.bot.source))
            view.add_item(button(style=discord.ButtonStyle.link, label="License", url=license_link))
            return await ctx.send(embed=source_embed, view=view)

        if command == "help":
            cmd = self.bot.help_command
        else:
            cmd = self.bot.get_command(command)
        if cmd is None:
            source_embed.description = "That command could not be found."
            return await ctx.send(embed=source_embed)

        if isinstance(cmd, commands.HelpCommand):
            lines, number_one = inspect.getsourcelines(type(command))
            src = command.__module__
        else:
            lines, number_one = inspect.getsourcelines(cmd.callback.__code__)
            src = cmd.callback.__module__

        path = f"{src.replace('.', '/')}.py"

        number_two = number_one + len(lines) - 1
        command = "help" if isinstance(command, commands.HelpCommand) else command
        link = f"{git_link}{path}#L{number_one}-L{number_two}"
        source_embed.description = (
            f"Click below for the source of `{command}`.\n" "Remember to follow the license.\n" "Made by avizum."
        )
        view.add_item(button(style=discord.ButtonStyle.link, label=f"Source for {command}", url=link))
        view.add_item(button(style=discord.ButtonStyle.link, label="License", url=license_link))
        await ctx.send(embed=source_embed, view=view)

    @source.autocomplete("command")
    async def source_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        commands = [
            c.qualified_name for c in list(self.bot.walk_commands()) if current in c.qualified_name and len(current) > 2
        ]
        to_return = [app_commands.Choice(name=cmd, value=cmd) for cmd in commands]
        return to_return[:25]

    @core.command(
        aliases=[
            "deleteallmydata",
            "clearalldata",
            "trashmydata",
            "deletaalldata",
            "databegone",
            "burnmydata",
            "byebyedata",
        ]
    )
    async def deletemydata(self, ctx: Context):
        """
        Delete all the data I have about you.

        This includes:
        Your timezone if you set it
        Your user id
        """
        embed = discord.Embed(
            title="Delete user data",
            description=(
                "Are you sure you want to delete all your user data?\n"
                "This will delete **everything** and it is **unrecoverable**."
            ),
            color=discord.Color.red(),
        )
        conf = await ctx.confirm(embed=embed)
        if conf.result:
            user_settings = ctx.database.get_user(ctx.author.id)
            highlights = ctx.database.get_highlights(ctx.author.id)
            if not user_settings and not highlights:
                return await ctx.send("You are not in my database.")
            if user_settings:
                await user_settings.delete()
            if highlights:
                await highlights.delete()
            return await ctx.send("Okay, I deleted all your data.")
        return await conf.message.edit(content="Aborted.")

    @core.command()
    async def error(self, ctx: Context, error_id: int | None = None):
        """
        Get some error about an error

        This will show the Traceback and if it has been fixed yet.
        If you have any ideas on how to fix it, You can DM Alpine or use the suggest command.
        """
        if error_id is None:
            return await ctx.send_help("error")
        query = "SELECT * FROM command_errors WHERE id=$1"
        error_info = await self.bot.database.pool.fetchrow(query, error_id)
        if not error_info:
            return await ctx.send("That is not a valid error id.")
        embed = discord.Embed(
            title=f"Error `#{error_info['id']}`",
            description=f"Error Information:```py\n{error_info['error']}```",
        )
        embed.add_field(
            name="Error status",
            value="Fixed" if error_info["fixed"] is True else "Not Fixed",
        )
        await ctx.send(embed=embed)

    @core.command(
        member_permissions="None, This is help for the paginator",
        bot_permissions="idk",
        hidden=True,
    )
    @core.is_owner()
    async def paginator(self, ctx: Context):
        """
        **How to use paginators**
        ⏮: Goes to the first page of the paginator
        ◀️: Goes back one page
        ▶️: Goes forward one page
        ⏭: Goes to the last page of the paginator
        ⏹: Stops the paginator
        1/x: Click on it to choose a page to jump to.
        """
