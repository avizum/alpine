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

import discord
import datetime
import psutil
import humanize
import pathlib
import inspect
import os

from discord.ext import commands
from utils import AvimetryContext, AvimetryBot, Timer


class BotInfo(commands.Cog, name="Bot Info"):
    """
    Commands about the bot
    """
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.avi.get_context(message, cls=AvimetryContext)
        if message.author == self.avi.user:
            return
        if message.content.lower == ((f"<@{self.avi.user.id}>", f"<@!{self.avi.user.id}>")):
            command = self.avi.get_command("prefix")
            await command(ctx)

    @commands.command()
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
        embed.add_field(name="Developer", value="avi#8771 (Main)")
        embed.add_field(name="Ping", value=f"`{round(self.avi.latency * 1000)}ms`")
        embed.add_field(name="Guild Count", value=f"{len(self.avi.guilds)} Guilds")
        embed.add_field(name="User Count", value=f"{len(self.avi.users)} Users")
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%")
        embed.add_field(name="Memory Usage", value=f"{used:,.2f}/{total} MB")
        embed.add_field(
            name="Bot Invite",
            value=f"[here]({self.avi.invite})",
        )
        embed.add_field(name="Commands", value=f"{len(self.avi.commands)} loaded")
        embed.add_field(name="Commands ran", value=self.avi.commands_ran)
        embed.add_field(name="Credits", value="Foxi#6626 (Avatar),\nDutchy#6127 (Help Command)\nLere#3303 (Tester)")
        embed.set_thumbnail(url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(brief="Get the bot's uptime")
    async def uptime(self, ctx: AvimetryContext):
        delta_uptime = datetime.datetime.utcnow() - self.avi.launch_time
        ue = discord.Embed(
            title="Current Uptime",
            description=humanize.precisedelta(delta_uptime, format="%.2g"),
        )
        await ctx.send(embed=ue)

    @commands.command(brief="Gets the bot's ping.")
    async def ping(self, ctx: AvimetryContext):
        with Timer() as api:
            await ctx.trigger_typing()
        with Timer() as db:
            await self.avi.pool.fetch("SELECT 1")
        ping_embed = discord.Embed(title="🏓 Pong!")
        ping_embed.add_field(
            name="Websocket Latency",
            value=f"`{self.avi.latency * 1000:,.2f} ms`",
            inline=False)
        ping_embed.add_field(
            name="Typing Latency",
            value=f"`{api.total_time * 1000:,.2f} ms`",
            inline=False)
        ping_embed.add_field(
            name="Database Latency",
            value=f"`{db.total_time * 1000:,.2f} ms`",
            inline=False)

        await ctx.send(embed=ping_embed)

    @commands.group(
        invoke_without_command=True,
        brief="Get the invite link for the bot"
    )
    async def invite(self, ctx: AvimetryContext):
        invite_embed = discord.Embed(
            title=f"{self.avi.user.name} Invite",
            description=(
                "Invite me to your server! Here is the invite link.\n"
                f"[Here]({str(discord.utils.oauth_url(self.avi.user.id, discord.Permissions(2147483647)))}) "
                "is the invite link."
            ),
        )
        invite_embed.set_thumbnail(url=self.avi.user.avatar_url)
        await ctx.send(embed=invite_embed)

    @invite.command(brief="Get the invite link for a bot in the server.")
    async def bot(self, ctx: AvimetryContext, bot: discord.Member):
        bot_invite = discord.Embed()
        bot_invite.set_thumbnail(url=bot.avatar_url)
        bot_invite.title = f"{bot.name} Invite"
        if bot.bot:
            bot_invite.description = (
                f"Invite {bot.name} to your server! Here is the invite link.\n"
                f"Click [here]({str(discord.utils.oauth_url(bot.id, discord.Permissions(2147483647)))}) for the invite!"
            )
        else:
            bot_invite.description = "That is not a bot. Make sure you mention a bot."
        await ctx.send(embed=bot_invite)

    @commands.command(
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

    @commands.command(brief="Request a feature to be added to the bot.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def request(self, ctx: AvimetryContext, *, request):
        request_channel = self.avi.get_channel(817093957322407956)
        req_send = discord.Embed(
            title=f"Request from {str(ctx.author)}",
            description=f"```{request}```"
        )
        await request_channel.send(embed=req_send)
        req_embed = discord.Embed(
            title="Request sent",
            description=(
                "Thank you for your request! Join the [support](https://discord.gg/KaqqPhfwS4) server to see if \n"
                "your request has been approved.\n"
                "Please note that spam requests will get you permanently blacklisted from this bot."
            )
        )
        req_embed.add_field(
            name="Your request",
            value=f"```{request}```"
        )
        await ctx.send(embed=req_embed)

    @commands.command(brief="Vote Now!")
    async def vote(self, ctx: AvimetryContext):
        top_gg = "https://top.gg/bot/756257170521063444/vote"
        bot_list = "https://discordbotlist.com/bots/avimetry/upvote"
        vote_embed = discord.Embed(
            title=f"Vote for {self.avi.user.name}",
            description=(
                f"**Vote on __top.gg__**\n[__`Vote Now`__]({top_gg})\n\n"
                f"**Vote on __discordbotlist.com__**\n[__`Vote Now`__]({bot_list})")
        )
        await ctx.send(embed=vote_embed)

    @commands.command(
        brief="Get the source of a command or bot."
    )
    async def source(self, ctx: AvimetryContext, *, command: str = None):
        source_embed = discord.Embed(
                title=f"{self.avi.user.name}'s source",
                timestamp=datetime.datetime.utcnow()
            )
        git_link = "https://github.com/avimetry/avimetry/blob/master/"
        license_link = "https://github.com/avimetry/avimetry/blob/master/LICENSE"
        if not command:
            if self.avi.user.id != 756257170521063444:
                source_embed.description = (
                    "This bot is an instance of [Avimetry](https://github.com/avimetry/avimetry), "
                    "Made by [avi](https://discord.com/users/750135653638865017). "
                    f"Follow the [license]({license_link})"
                )
            else:
                source_embed.description = (
                    "Here is my [source](https://github.com/avimetry/avimetry). "
                    "I am made by [avi](https://discord.com/users/750135653638865017).\n"
                    f"Follow the [license]({license_link})"
                )
            return await ctx.send(embed=source_embed)

        if command == "help":
            command = self.avi.help_command
        else:
            command = self.avi.get_command(command)
        if not command:
            return await ctx.send("Couldn't find command.")

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

    @commands.command(
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
            user_settings = self.avi.cache.users.get(ctx.author.id)
            if not user_settings:
                return await ctx.send("You are not in my database.")
            query = (
                "DELETE FROM user_settings "
                "WHERE user_id=$1"
            )
            await self.avi.pool.execute(query, ctx.author.id)
            self.avi.cache.users.pop(ctx.author.id)
            return await ctx.send("Okay, I deleted all your data.")
        return await ctx.send("Aborted.")

    @commands.group(invoke_without_command=True)
    async def error(self, ctx: AvimetryContext, error_id: int = None):
        if error_id is None:
            return await ctx.send_help("error")
        query = "SELECT * FROM command_errors WHERE id=$1"
        error_info = await self.avi.pool.fetchrow(query, error_id)
        if not error_info:
            return await ctx.send("That is not a valid error id.")
        embed = discord.Embed(
            title=f"Error `#{error_info['id']}`",
            description=f"Error Information:```py\n{error_info['error']}```"
        )
        embed.add_field(name="Error status", value="Fixed" if error_info["fixed"] is True else "Not Fixed")
        await ctx.send(embed=embed)

    @error.command()
    @commands.is_owner()
    async def fix(self, ctx: AvimetryContext, error_id: int = None):
        if error_id is None:
            return await ctx.send_help("error")
        query = "SELECT * FROM command_errors WHERE id=$1"
        error_info = await self.avi.pool.fetchrow(query, error_id)
        if not error_info:
            return await ctx.send("That is not a valid error id")
        query = "UPDATE command_errors SET fixed=$1 WHERE id=$2"
        await self.avi.pool.execute(query, True, error_id)


def setup(avi):
    avi.add_cog(BotInfo((avi)))
