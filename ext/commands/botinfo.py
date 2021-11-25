"""
Commands about the bot
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

import discord
import datetime
import psutil
import humanize
import pathlib
import os
import inspect
import core

from typing import Union
from discord.ext import commands
from topgg import NotFound
from utils import AvimetryContext, AvimetryBot, Timer


class BotInfo(commands.Cog, name="Bot Info"):
    """
    Bot Information commands
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.emoji = "\U00002139"
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.process = psutil.Process(os.getpid())
        self.request_wh = discord.Webhook.from_url(
            self.bot.settings["webhooks"]["request_log"],
            session=self.bot.session
        )

    @core.Cog.listener()
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
    async def news(self, ctx: AvimetryContext):
        """
        Show the bot's news.
        """
        embed = discord.Embed(title="\U0001f4f0 Avimetry News", description=self.bot.news)
        await ctx.send(embed=embed)

    @core.command()
    async def about(self, ctx: AvimetryContext):
        """
        Show some information about Avimetry.
        """
        embed = discord.Embed(title="Info about Avimetry")
        embed.add_field(name="Latest News", value=self.bot.news, inline=False)
        async with ctx.channel.typing():
            async with self.bot.session.get("https://api.github.com/repos/avimetry/avimetry/commits") as resp:
                items = await resp.json()
        try:
            commits = "\n".join(f"[`{cm['sha'][:7]}`]({cm['html_url']}) {cm['commit']['message']}" for cm in items[:3])
        except KeyError:
            commits = "Error lol"
        embed.add_field(name="Latest Commits", value=commits, inline=False)
        delta_uptime = datetime.datetime.now(datetime.timezone.utc) - self.bot.launch_time
        embed.add_field(
            name="Info",
            value=f"Up for {humanize.precisedelta(delta_uptime)},\n`{round(self.bot.latency*1000)}ms` latency")
        embed.add_field(name="Stats", value=f"{len(self.bot.guilds)} Servers\n{len(self.bot.users)} Users")
        embed.set_thumbnail(url=ctx.me.display_avatar.url)
        owner = self.bot.get_user(750135653638865017)
        embed.set_footer(text=f"Made by {owner} :)", icon_url=owner.display_avatar.url)
        await ctx.send(embed=embed)

    @core.command(name="credits")
    async def avimetry_credits(self, ctx: AvimetryContext):
        """
        List of people that have contributed to Avimetry.

        If you want to contribute, Check out the GitHub repo.
        """
        credit_list = [
            (self.bot.get_user(750135653638865017), 'Developer', 'https://github.com/avizum'),
            (self.bot.get_user(80088516616269824), 'Developer of discord.py', 'https://github.com/Rapptz'),
            (self.bot.get_user(547280209284562944), 'Testing', 'https://github.com/LereUwU'),
            (self.bot.get_user(672122220566413312), 'Avatar', 'https://discord.com/users/672122220566413312'),
            (self.bot.get_user(171539705043615744), 'Help Command, Error Tracking', 'https://github.com/iDutchy'),
            (self.bot.get_user(733370212199694467), 'Contributor', 'https://github.com/MrArkon/'),
            (self.bot.get_user(797044260196319282), 'Noob', 'https://github.com/jottew')
        ]

        embed = discord.Embed(
            title="Credits",
            description="\n".join(f"[{user}]({credit}): {role}" for user, role, credit in credit_list)
        )

        await ctx.send(embed=embed)

    @core.command(aliases=["github"])
    async def commits(self, ctx: AvimetryContext):
        """
        Gets the recent commits in the Avimetry repo.

        This shows the recent commits on the repo.
        You can contribute on the repo.
        """
        async with ctx.channel.typing():
            async with self.bot.session.get("https://api.github.com/repos/avimetry/avimetry/commits") as resp:
                items = await resp.json()
        try:
            commit_list = [f"[`{cm['sha'][:7]}`]({cm['html_url']}) {cm['commit']['message']}" for cm in items[:10]]
        except KeyError:
            return await ctx.send("An error occured while trying to get the commits. Try again later.")
        embed = discord.Embed(title="Recent commits", description="\n".join(commit_list))
        embed.set_footer(text="Contribute to Avimetry by doing magic.")
        await ctx.send(embed=embed)

    @core.command()
    async def uptime(self, ctx: AvimetryContext):
        """
        Check how long the bot has been up for.
        """
        delta_uptime = datetime.datetime.now(datetime.timezone.utc) - self.bot.launch_time
        ue = discord.Embed(
            title="Current Uptime",
            description=humanize.precisedelta(delta_uptime, format="%.2g"),
        )
        await ctx.send(embed=ue)

    @core.command(brief="Get the bot's latencies")
    async def ping(self, ctx: AvimetryContext):
        """
        Check the bot's latencies.

        Websocket: latency between the bot and Discord's servers.
        Typing: how long it takes to send typing to the channel.
        Database: how long it takes to query the database.
        """
        async with Timer() as api:
            await ctx.trigger_typing()
        async with Timer() as db:
            await self.bot.pool.execute("SELECT 1")
        ping_embed = discord.Embed(title="Pong!")
        ping_embed.add_field(
            name="<:avimetry:877445146709463081> Websocket Latency",
            value=f"`{self.bot.latency * 1000:,.2f} ms`",
            inline=False)
        ping_embed.add_field(
            name="<a:typing:877445218729861190> Typing Latency",
            value=f"`{api.total_time * 1000:,.2f} ms`",
            inline=False)
        ping_embed.add_field(
            name="<:pgsql:877445172093403166> Database Latency",
            value=f"`{db.total_time * 1000:,.2f} ms`",
            inline=False)
        await ctx.send(embed=ping_embed)

    @core.command()
    async def hello(self, ctx: AvimetryContext):
        """
        Hello!
        """
        embed = discord.Embed(
            title='\U0001f44b Hey, I am Avimetry!',
            description=f'Hello {ctx.author.mention}, I am a bot made by [avizum.](https://github.com/avizum)',
            color=ctx.guild.owner.color
        )
        embed.add_field(name=f'{ctx.clean_prefix}help', value='Sends the help page.', inline=False)
        embed.add_field(
            name=f'{ctx.clean_prefix}prefix add',
            value='Adds a prefix to this server. (You can have up to 15 prefixes)',
            inline=False
        )
        embed.add_field(name=f'{ctx.clean_prefix}about', value='Show some info about the bot.', inline=False)
        embed.add_field(name=f'{ctx.clean_prefix}vote', value='Support Avimetry by voting! Thank you!', inline=False)
        embed.set_footer(text='Made by avizum :)')
        await ctx.send(embed=embed)

    @core.group(invoke_without_command=True)
    async def invite(self, ctx: AvimetryContext, bot: Union[discord.Member, discord.User] = None):
        """
        Invite me to your server.

        If you mention a bot, I will try to find their Top.GG page and send it. If I can't find it, then
        I will generate an invite link and send it.
        """
        view = discord.ui.View(timeout=None)
        if bot is None:
            invite_embed = discord.Embed(
                title=f"{self.bot.user.name} Invite",
                description="Invite me to your server! Here is the invite link.",
            )
            invite_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, url=self.bot.invite, label="Invite me"))
            view.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    url=self.bot.support,
                    label="Avimetry support server")
                )
            await ctx.send(embed=invite_embed, view=view)
        elif bot.bot:
            invite_embed = discord.Embed(title=f"{bot.name} Invite")
            invite_embed.set_thumbnail(url=bot.display_avatar.url)
            try:
                top = await self.bot.topgg.get_bot_info(bot.id)
                invite_embed.description = f"Invite {bot.name} to your server! Here is the invite link."
                link = f"https://top.gg/bot/{bot.id}"
                view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{bot.name} (top.gg)", url=link))
                view.add_item(discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label=f"{bot.name}'s support server",
                        url=f"https://discord.gg/{top.support}"
                    )
                )
            except NotFound:
                invite_embed.description = f"Invite {bot.name} to your server! Here is the invite link."
                link = str(discord.utils.oauth_url(bot.id, permissions=discord.Permissions(8)))
                view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=f"{bot.name} Invite", url=link))
            await ctx.send(embed=invite_embed, view=view)
        else:
            await ctx.send("That is not a bot.")

    @core.command(aliases=["lc", "linec", "lcount"])
    async def linecount(self, ctx):
        """
        Check how many lines of code the bot has.
        """
        path = pathlib.Path('./')
        comments = coros = funcs = classes = lines = imports = files = char = 0
        for item in path.rglob('*.py'):
            if str(item).startswith("venv"):
                continue
            files += 1
            with item.open() as of:
                for line in of.readlines():
                    line = line.strip()
                    if line.startswith('class'):
                        classes += 1
                    if line.startswith('def'):
                        funcs += 1
                    if line.startswith('async def'):
                        coros += 1
                    if 'import' in line:
                        imports += 1
                    if '#' in line:
                        comments += 1
                    lines += 1
                    char += len(line)
        embed = discord.Embed(
            title="Line Count",
            description=(
                "```py\n"
                f"Files: {files:,}\n"
                f"Characters: {char:,}\n"
                f"Lines: {lines:,}\n"
                f"Classes: {classes:,}\n"
                f"Functions: {funcs:,}\n"
                f"Coroutines: {coros:,}\n"
                f"Comments: {comments:,}"
                "```"
            )
        )
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(style=discord.ui.Button, url=self.bot.support, label="Source"))
        await ctx.send(embed=embed, view=view)

    @core.command(brief="Request a feature to be added to the bot.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def request(self, ctx: AvimetryContext, *, request):
        """
        Request a feature to be added to Avimetry.

        Spamming this command or sending spam requests will get you blacklisted from the bot.
        """
        conf = await ctx.confirm(f"Are sure you want to send this request?\n> {request}")
        if conf.result:

            req_send = discord.Embed(
                title=f'Request from {ctx.author}', description=f"```{request}```"
            )

            await self.request_wh.send(embed=req_send)
            req_embed = discord.Embed(
                title="Request sent",
                description=(
                    "Thank you for your request! It has been sent to the support server. "
                    f"Spam will get you permanently blacklisted from this {self.bot.user.name}."
                )
            )
            req_embed.add_field(
                name="Your request",
                value=f"```{request}```"
            )
            return await ctx.send(embed=req_embed)
        return await conf.message.edit(content="Okay, I will not send it.")

    @core.command()
    async def support(self, ctx: AvimetryContext):
        """
        Send the bot's support server link.
        """
        await ctx.send(self.bot.support)

    @core.command()
    async def vote(self, ctx: AvimetryContext):
        """
        Support Avimetry by voting!
        """
        view = discord.ui.View()
        links = [
            ("Top.gg", "https://top.gg/bot/756257170521063444/vote"),
            ("Discord Bot List", "https://discordbotlist.com/bots/avimetry/upvote"),
            ("Discord Boats", "https://discord.boats/bot/756257170521063444/vote")
        ]
        for name, link in links:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.link, label=name, url=link))
        vote_embed = discord.Embed(
            title=f"Vote for {self.bot.user.name}",
            description="Thank you for voting for me!\nYour support is greatly appreciated :)"
        )
        vote_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=vote_embed, view=view)

    # Please do not remove this command.
    # - avizum
    @core.command()
    async def source(self, ctx: AvimetryContext, *, command: str = None):
        """
        Send the bot's source or a source of a command.

        Typing a command will send the source of a command instead.
        """
        button = discord.ui.Button
        view = discord.ui.View(timeout=None)
        source_embed = discord.Embed(
                title=f"{self.bot.user.name}'s source",
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
        git_link = f"{self.bot.source}/blob/master/"
        license_link = f"{self.bot.source}/blob/master/LICENSE"
        if not command:
            if self.bot.user.id != 756257170521063444:
                source_embed.description = (
                    "This bot is an instance of Avimetry.\n"
                    "Click below for the source."
                    "Made by avizum\n"
                    "Follow the license"
                )
            else:
                source_embed.description = (
                    "Click below for the source of Avimetry.\n"
                    "I am made by avizum\n"
                    "Follow the license and please star :)"
                )
            view.add_item(button(style=discord.ButtonStyle.link, label="Source", url=self.bot.source))
            view.add_item(button(style=discord.ButtonStyle.link, label="License", url=license_link))
            return await ctx.send(embed=source_embed, view=view)

        if command == "help":
            command = self.bot.help_command
        else:
            command = self.bot.get_command(command)
        if not command:
            source_embed.description = "That command could not be found."
            return await ctx.send(embed=source_embed)

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
            f"Click below for the source of `{command}`.\n"
            "Remember to follow the license.\n"
            "Made by avizum."
            )
        view.add_item(button(style=discord.ButtonStyle.link, label=f"Source for {command}", url=link))
        view.add_item(button(style=discord.ButtonStyle.link, label="License", url=license_link))
        await ctx.send(embed=source_embed, view=view)

    @core.command(
        aliases=[
            "deleteallmydata", "clearalldata",
            "trashmydata", "deletaalldata",
            "databegone", "burnmydata",
            "byebyedata"
        ]
    )
    async def deletemydata(self, ctx: AvimetryContext):
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
            color=discord.Color.red()
        )
        conf = await ctx.confirm(embed=embed)
        if conf.result:
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
        return await conf.message.edit(content="Aborted.")

    @core.command()
    async def error(self, ctx: AvimetryContext, error_id: int = None):
        """
        Get some error about an error

        This will show the Traceback and if it has been fixed yet.
        If you have any ideas on how to fix it, You can DM Avimetry or use the suggest command.
        """
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

    @core.command(user_permissions="None, This is help for the paginator", bot_permissions="idk", hidden=True)
    @core.is_owner()
    async def paginator(self, ctx):
        """
        **How to use paginators**
        ⏮: Goes to the first page of the paginator
        ◀️: Goes back one page
        ▶️: Goes forward one page
        ⏭: Goes to the last page of the paginator
        ⏹: Stops the paginator
        1/x: Click on it to choose a page to jump to.
        """
        return


def setup(bot: AvimetryBot):
    bot.add_cog(BotInfo(bot))
