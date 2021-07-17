"""
Commands about the bot
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

from typing import Union
import discord
import datetime
import psutil
import humanize
import pathlib
import inspect
import os

from discord.ext import commands
from topgg import NotFound
from utils import AvimetryContext, AvimetryBot, Timer
from utils import core


class BotInfo(commands.Cog, name="Bot Info"):
    """
    Commands about the bot
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.request_wh = discord.Webhook.from_url(
            self.bot.settings["webhooks"]["request_log"],
            adapter=discord.AsyncWebhookAdapter(self.bot.session)
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.bot.get_context(message, cls=AvimetryContext)
        if message.author == self.bot.user:
            return
        if message.content in [
            f"<@{self.bot.user.id}>",
            f"<@!{self.bot.user.id}>",
        ]:
            command = self.bot.get_command("prefix")
            ctx.command = command
            await command(ctx)

    @core.command()
    async def about(self, ctx: AvimetryContext):
        embed = discord.Embed(title="Info about Avimetry")
        embed.add_field(
            name="Latest Updates",
            value="Vote Now at [top.gg](https://top.gg/bot/756257170521063444/vote)",
            inline=False
        )
        pid = psutil.Process(os.getpid())
        used = pid.memory_info().rss / 1024 ** 2
        total = psutil.virtual_memory().total / 1024 ** 2
        developer = self.bot.get_user(750135653638865017)
        embed.add_field(name="Developer", value=f"{developer} (Main)")
        embed.add_field(name="Ping", value=f"`{round(self.bot.latency * 1000)}ms`")
        embed.add_field(name="Guild Count", value=f"{len(self.bot.guilds)} Guilds")
        embed.add_field(name="User Count", value=f"{len(self.bot.users)} Users")
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%")
        embed.add_field(name="Memory Usage", value=f"{used:,.2f}/{total} MB")
        embed.add_field(
            name="Bot Invite",
            value=f"[here]({self.bot.invite})",
        )
        embed.add_field(name="Commands", value=f"{len(self.bot.commands)} loaded")
        embed.add_field(name="Commands ran", value=self.bot.commands_ran)
        tester = self.bot.get_user(547280209284562944)
        avatar = self.bot.get_user(672122220566413312)
        help_command = self.bot.get_user(171539705043615744)
        cont_one = self.bot.get_user(733370212199694467)
        embed.add_field(
            name="Credits",
            value=(
                f"{avatar} (Avatar),\n"
                f"{help_command} (Help Command)\n"
                f"{tester} (Tester)\n"
                f"{cont_one} (Contributor)"
            )
        )
        embed.set_thumbnail(url=ctx.me.avatar_url)
        embed.set_footer(text="Want to be a contributor? Use the suggest command or create a PR on the github repo")
        await ctx.send(embed=embed)

    @core.command()
    async def credits(self, ctx: AvimetryContext):
        embed = discord.Embed(
            title="Credits",
            description="avizum#8771: Main Developer"
        )
        await ctx.send(embed=embed)

    @core.command(brief="Get the bot's uptime")
    async def uptime(self, ctx: AvimetryContext):
        delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
        ue = discord.Embed(
            title="Current Uptime",
            description=humanize.precisedelta(delta_uptime, format="%.2g"),
        )
        await ctx.send(embed=ue)

    @core.command(brief="Gets the bot's ping.")
    async def ping(self, ctx: AvimetryContext):
        async with Timer() as api:
            await ctx.trigger_typing()
        async with Timer() as db:
            await self.bot.pool.execute("SELECT 1")
        ping_embed = discord.Embed(title="🏓 Pong!")
        ping_embed.add_field(
            name="<:avimetry:848820318117691432> Websocket Latency",
            value=f"`{self.bot.latency * 1000:,.2f} ms`",
            inline=False)
        ping_embed.add_field(
            name="<a:typing:865110878408278038> Typing Latency",
            value=f"`{api.total_time * 1000:,.2f} ms`",
            inline=False)
        ping_embed.add_field(
            name="<:pgsql:865110950825951242> Database Latency",
            value=f"`{db.total_time * 1000:,.2f} ms`",
            inline=False)
        await ctx.send(embed=ping_embed)

    @core.command()
    async def hello(self, ctx: AvimetryContext):
        await ctx.send(f'Hello, {ctx.author}, I am a bot made my avizum#8771!')

    @core.group(
        invoke_without_command=True,
        brief="Get the invite link for the bot or another bot"
    )
    async def invite(self, ctx: AvimetryContext, bot: Union[discord.Member, discord.User] = None):
        if bot is None:
            invite_embed = discord.Embed(
                title=f"{self.bot.user.name} Invite",
                description=(
                    "Invite me to your server! Here is the invite link.\n"
                    f"[Here]({str(discord.utils.oauth_url(self.bot.user.id, discord.Permissions(8)))}) "
                    "is the invite link."
                ),
            )
            invite_embed.set_thumbnail(url=self.bot.user.avatar_url)
            await ctx.send(embed=invite_embed)
        elif bot.bot:
            invite_embed = discord.Embed(title=f"{bot.name} Invite")
            try:
                await self.bot.topgg.get_bot_info(bot.id)
                invite_embed.description = (
                    f"Invite {bot.name} to your server! Here is the invite link.\n"
                    f"[Here! (top.gg)](https://top.gg/bot/{bot.id})"
                )
            except NotFound:
                invite_embed.description = (
                    f"Invite {bot.name} to your server! Here is the invite link.\n"
                    f"[Click here!]({str(discord.utils.oauth_url(bot.id, discord.Permissions(8)))})"
                )
            await ctx.send(embed=invite_embed)
        else:
            await ctx.send("That is not a bot.")

    @core.command(
        aliases=["lc", "linec", "lcount"],
        brief="Gets the amount of lines this bot has."
    )
    async def linecount(self, ctx):
        path = pathlib.Path('./')
        comment_count = corutine_count = function_count = class_count = line_count = file_count = 0
        for files in path.rglob('*.py'):
            if str(files).startswith("venv"):
                continue
            file_count += 1
            with files.open() as of:
                for line in of.readlines():
                    line = line.strip()
                    if line.startswith('class'):
                        class_count += 1
                    if line.startswith('def'):
                        function_count += 1
                    if line.startswith('async def'):
                        corutine_count += 1
                    if '#' in line:
                        comment_count += 1
                    line_count += 1
        embed = discord.Embed(
            title="Line Count",
            description=(
                "```py\n"
                f"Files: {file_count}\n"
                f"Lines: {line_count}\n"
                f"Classes: {class_count}\n"
                f"Functions: {function_count}\n"
                f"Coroutines: {corutine_count}\n"
                f"Comments: {comment_count}"
                "```"
            )
        )
        await ctx.send(embed=embed)

    @core.command(brief="Request a feature to be added to the bot.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def request(self, ctx: AvimetryContext, *, request):
        req_send = discord.Embed(
            title=f"Request from {str(ctx.author)}",
            description=f"```{request}```"
        )
        await self.request_wh.send(embed=req_send)
        req_embed = discord.Embed(
            title="Request sent",
            description=(
                "Thank you for your request! It has been sent to the [support](https://discord.gg/KaqqPhfwS4) server. "
                f"Spam will get you permanently blacklisted from this {self.bot.user.name}."
            )
        )
        req_embed.add_field(
            name="Your request",
            value=f"```{request}```"
        )
        await ctx.send(embed=req_embed)

    @core.command()
    async def support(self, ctx: AvimetryContext):
        await ctx.send(self.bot.support)

    @core.command(brief="Vote Now!")
    async def vote(self, ctx: AvimetryContext):
        top_gg = "https://top.gg/bot/756257170521063444/vote"
        bot_list = "https://discordbotlist.com/bots/avimetry/upvote"
        vote_embed = discord.Embed(
            title=f"Vote for {self.bot.user.name}",
            description=(
                f"**Vote on __top.gg__**\n[__`Vote Now`__]({top_gg})\n\n"
                f"**Vote on __discordbotlist.com__**\n[__`Vote Now`__]({bot_list})")
        )
        await ctx.send(embed=vote_embed)

    @core.command(
        brief="Get the source of a command or bot."
    )
    async def source(self, ctx: AvimetryContext, *, command: str = None):
        source_embed = discord.Embed(
                title=f"{self.bot.user.name}'s source",
                timestamp=datetime.datetime.utcnow()
            )
        git_link = "https://github.com/avimetry/avimetry/blob/master/"
        license_link = "https://github.com/avimetry/avimetry/blob/master/LICENSE"
        if not command:
            if self.bot.user.id != 756257170521063444:
                source_embed.description = (
                    "This bot is an instance of [Avimetry](https://github.com/avimetry/avimetry), "
                    "Made by [avizum#8771](https://discord.com/users/750135653638865017). "
                    f"Follow the [license]({license_link})"
                )
            else:
                source_embed.description = (
                    "Here is my [source](https://github.com/avimetry/avimetry). "
                    "I am made by [avizum#8771](https://discord.com/users/750135653638865017).\n"
                    f"Follow the [license]({license_link})"
                )
            return await ctx.send(embed=source_embed)

        if command == "help":
            command = self.bot.help_command
        else:
            command = self.bot.get_command(command)
        if not command:
            return await ctx.send(f'Command "{command}" not found.')

        if isinstance(command, commands.HelpCommand):
            lines, number_one = inspect.getsourcelines(type(command))
            src = command.__module__
        else:
            lines, number_one = inspect.getsourcelines(command.callback.__code__)
            src = command.callback.__module__

        path = f"{src.replace('.', '/')}.py"

        number_two = number_one + len(lines) - 1
        command = "help" if isinstance(command, commands.HelpCommand) else command
        link = f"{git_link}{path}#L{number_one}-L{number_two}"
        source_embed.description = (
            f"[Here is the source]({link}) for `{command}`. "
            f"Follow the [license]({license_link})."
            )
        await ctx.send(embed=source_embed)

    @core.command(
        aliases=[
            "deleteallmydata", "clearalldata",
            "trashmydata", "deletaalldata",
            "databegone", "burnmydata",
            "byebyedata"
        ]
    )
    async def deletemydata(self, ctx: AvimetryContext):
        embed = discord.Embed(
            title="Delete user data",
            description=(
                "Are you sure you want to delete all your user data?\n"
                "This will delete **everything** and it is **unrecoverable**."
            ),
            color=discord.Color.red()
        )
        conf = await ctx.confirm(embed=embed)
        if conf:
            user_settings = self.bot.cache.users.get(ctx.author.id)
            if not user_settings:
                return await ctx.send("You are not in my database.")
            query = (
                "DELETE FROM user_settings "
                "WHERE user_id=$1"
            )
            await self.bot.pool.execute(query, ctx.author.id)
            self.bot.cache.users.pop(ctx.author.id)
            return await ctx.send("Okay, I deleted all your data.")
        return await ctx.send("Aborted.")

    @core.command()
    async def error(self, ctx: AvimetryContext, error_id: int = None):
        if error_id is None:
            return await ctx.send_help("error")
        query = "SELECT * FROM command_errors WHERE id=$1"
        error_info = await self.bot.pool.fetchrow(query, error_id)
        if not error_info:
            return await ctx.send("That is not a valid error id.")
        embed = discord.Embed(
            title=f"Error `#{error_info['id']}`",
            description=f"Error Information:```py\n{error_info['error']}```"
        )
        embed.add_field(name="Error status", value="Fixed" if error_info["fixed"] is True else "Not Fixed")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(BotInfo((bot)))
