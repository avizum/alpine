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
import json
import random
from typing import TYPE_CHECKING

import asyncgist
import discord
import pytz
from discord.ext import commands, menus
from doc_search import AsyncScraper
from jishaku.codeblocks import codeblock_converter

import core
from utils import Emojis, Paginator, PaginatorEmbed, timestamp

if TYPE_CHECKING:
    from datetime import datetime

    from core import Bot, Context


class TimeZoneError(commands.BadArgument):
    def __init__(self, argument: str) -> None:
        self.argument = argument
        super().__init__(
            f'Timezone "{argument}" was not found. [Here]'
            "(<https://gist.github.com/Soheab/3bec6dd6c1e90962ef46b8545823820d>) "
            "are all the valid timezones you can use."
        )


class RTFMPageSource(menus.ListPageSource):
    def __init__(self, ctx: Context, items: list[str], query: str) -> None:
        super().__init__(items, per_page=12)
        self.ctx: Context = ctx
        self.items: list[str] = items
        self.query: str = query

    async def format_page(self, menu: menus.Menu, page: list[str]) -> discord.Embed:
        embed = PaginatorEmbed(
            ctx=self.ctx,
            description=(
                "\n".join(f"[`{k.replace('discord.', '').replace('discord.ext.commands.', '')}`]({v})" for k, v in page)
            ),
        )
        embed.set_footer(text=f"Search results for {self.query}")
        return embed


class Meta(core.Cog):
    """
    Extra commands that do not lie in any specific category.
    """

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.load_time: datetime = dt.datetime.now(dt.timezone.utc)
        self.scraper: AsyncScraper = AsyncScraper(self.bot.loop, self.bot.session)

    @core.command()
    @core.cooldown(1, 300, commands.BucketType.user)
    async def poll(self, ctx: Context, question, *options: str):
        """
        Send a poll for people to vote to.

        The first option will be the title.
        You can have up to 10 other options in a poll.
        """
        if len(options) < 2:
            raise commands.BadArgument("You need to have at least two options in the poll.")
        if len(options) > 10:
            raise commands.BadArgument("You can only have ten options in a poll")
        if len(options) == 3 and options[0] == "yes" and options[1] == "maybe" and options[2] == "no":
            reactions = [
                Emojis.GREEN_TICK,
                Emojis.GRAY_TICK,
                Emojis.RED_TICK,
            ]
        elif len(options) == 2 and options[0].lower() == "yes" and options[1].lower() == "no":
            reactions = [
                Emojis.GREEN_TICK,
                Emojis.RED_TICK,
            ]
        else:
            reactions = [
                "1️⃣",
                "2️⃣",
                "3️⃣",
                "4️⃣",
                "5️⃣",
                "6️⃣",
                "7️⃣",
                "8️⃣",
                "9️⃣",
                "🔟",
            ]
        description = []
        for x, option in enumerate(options):
            description += f"\n\n{reactions[x]} {option}"
        embed = discord.Embed(title=question, description="".join(description))
        react_message = await ctx.channel.send(embed=embed)
        for reaction in reactions[: len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(text=f"Poll from: {ctx.author}\nMessage ID: {react_message.id}")

        await react_message.edit(embed=embed)

    @core.command()
    @core.cooldown(1, 1, commands.BucketType.member)
    async def pick(self, ctx: Context, *, options: str):
        """
        Pick one of your options you provided.

        You can use "or" to seperate, or "," to seperate options.
        """
        opt = options.split("or")
        if len(opt) != 2:
            opt = options.split(",")

        return await ctx.send(random.choice(opt))

    @core.command(hybrid=True, aliases=["ui", "uinfo", "whois", "memberinfo", "mi", "minfo", "user", "member"])
    @core.cooldown(1, 15, commands.BucketType.user)
    @core.describe(member="Person to get info about.")
    async def userinfo(self, ctx: Context, *, member: discord.Member | discord.User = commands.Author):
        """
        Get info about a user.

        This works with any user on Discord.
        """
        if isinstance(member, discord.User):
            ie = discord.Embed(
                title="User Information",
                description="This user in not in this server",
                timestamp=dt.datetime.now(dt.timezone.utc),
                color=member.color,
            )
            ie.add_field(name="User Name", value=str(member))
            ie.add_field(name="User ID", value=member.id)
            ie.add_field(
                name="Creation Date",
                value=f"{timestamp(member.created_at)} ({timestamp(member.created_at):R})",
                inline=False,
            )
        else:
            if ctx.interaction:
                member = ctx.guild.get_member(member.id) or member
            userroles = ["@everyone"]
            userroles.extend(roles.mention for roles in member.roles)
            userroles.remove(ctx.guild.default_role.mention)
            ie = discord.Embed(
                title="Member Information",
                timestamp=dt.datetime.now(dt.timezone.utc),
                color=member.color,
            )
            ie.add_field(name="User Name", value=str(member))
            ie.add_field(name="User ID", value=member.id)
            if member.nick:
                ie.add_field(name="Nickname", value=member.nick)

            sort = sorted(ctx.guild.members, key=lambda m: getattr(m, "joined_at"))
            pos = f"{sort.index(member) + 1:,} of {len(ctx.guild.members):,}"
            assert member.joined_at is not None
            ie.add_field(
                name="Join Date",
                value=f"{timestamp(member.joined_at)} ({timestamp(member.joined_at):R})\nJoin Position: {pos}",
                inline=False,
            )
            ie.add_field(
                name="Account Creation Date",
                value=f"{timestamp(member.created_at)} ({timestamp(member.created_at):R})",
                inline=False,
            )
            top_role = member.top_role.mention
            if top_role != ctx.guild.default_role.mention:
                ie.add_field(name="Top Role", value=top_role, inline=False)
            if len(userroles) >= 40:
                userroles = userroles[:40]
                userroles.append("...")
            ie.add_field(
                name=f"Roles [{len(member.roles)}]",
                value=", ".join(userroles),
                inline=False,
            )
            if member.public_flags.value > 0:
                flags = []
                for flag, value in member.public_flags:
                    new = flag.replace(flag, Emojis.BADGES.get(flag, flag))
                    flag_name = flag.replace("bot_http_interactions", "interactions_only")
                    if value is True:
                        if new == flag_name:
                            flags.append(flag_name.replace("_", " ").title())
                            continue
                        flags.append(f"{new} | {flag_name.replace('_', ' ').title()}")
                if ctx.guild.owner and ctx.guild.owner == member:
                    flags.append(f"{Emojis.BADGES["guild_owner"]} | Server Owner")
                ie.add_field(name=f"Badges [{len(flags)}]", value=",\n".join(flags))
            if member.status:
                replace = ("dnd", "do not disturb")
                desktop = member.desktop_status.name
                mobile = member.mobile_status.name
                web = member.web_status.name
                ie.add_field(
                    name="Status",
                    value=(
                        f"Desktop: {Emojis.STATUSES.get(desktop)} | {desktop.replace(*replace).title()}\n"
                        f"Mobile: {Emojis.STATUSES.get(mobile)} | {mobile.replace(*replace).title()}\n"
                        f"Web: {Emojis.STATUSES.get(web)} | {web.replace(*replace).title()}"
                    ),
                    inline=False,
                )

        ie.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=ie)

    @core.command()
    @core.is_owner()
    async def roleinfo(self, ctx: Context, role: discord.Role):
        embed = discord.Embed(title="Role Info")
        embed.add_field(name="Created At", value=f"{timestamp(role.created_at)}")
        embed.add_field(name="Role ID", value=role.id)

    @core.group(aliases=["members", "mc"])
    async def membercount(self, ctx: Context):
        """
        Show the member count.
        """
        tmc = len([m for m in ctx.guild.members if not m.bot])
        tbc = len([m for m in ctx.guild.members if m.bot])
        amc = ctx.guild.member_count
        mce = discord.Embed(title=f"Member Count for {ctx.guild.name}")
        mce.add_field(name="Members:", value=f"{tmc} members", inline=False)
        mce.add_field(name="Bots:", value=f"{tbc} bots", inline=False)
        mce.add_field(name="Total Members:", value=f"{amc} members", inline=False)
        await ctx.send(embed=mce)

    @membercount.command()
    async def role(self, ctx: Context, role: discord.Role):
        """
        Show the members in a role.
        """
        tmc = sum(not m.bot for m in role.members)
        tbc = sum(m.bot for m in role.members)
        mce = discord.Embed(title=f"Members in role: {role}")
        mce.add_field(name="Members:", value=f"{tmc} members", inline=False)
        mce.add_field(name="Bots:", value=f"{tbc} bots", inline=False)
        mce.add_field(name="Members", value=", ".join(i.mention for i in role.members[:42]))
        await ctx.send(embed=mce)

    @core.command()
    async def avatar(self, ctx: Context, member: discord.Member | discord.User = commands.Author):
        """
        Sends the avatar of a member.
        """
        member = member or ctx.author

        urls = (
            f"[`png`]({member.display_avatar.replace(format='png')}) | "
            f"[`jpeg`]({member.display_avatar.replace(format='jpeg')}) | "
            f"[`webp`]({member.display_avatar.replace(format='webp')})"
        )

        if member.display_avatar.is_animated():
            urls += f" | [`gif`]({member.display_avatar.replace(format='gif')})"

        embed = discord.Embed(title=f"{member}'s avatar", description=urls)
        avatar = member.display_avatar.url
        embed.set_image(url=avatar)
        await ctx.send(embed=embed)

    @core.command()
    @core.cooldown(2, 10, commands.BucketType.guild)
    async def banner(self, ctx: Context, member: discord.Member | discord.User | None = None):
        """
        Send the banner of a member.

        If they have no banner and have an accent color, the accent color will be sent instead.
        """
        member = member or ctx.author
        fetched = await self.bot.fetch_user(member.id)
        banner = fetched.banner
        if banner:
            embed = discord.Embed(title=f"{member}'s banner")
            embed.set_image(url=banner.url)
        elif fetched.accent_color:
            embed = discord.Embed(
                description=f"This person does not have a banner. Their accent color is {fetched.accent_color}.",
                color=fetched.accent_color,
            )
        else:
            return await ctx.send("This person does not have a banner.")
        return await ctx.send(embed=embed)

    @core.command(invoke_without_command=True)
    async def qr(self, ctx: Context, *, content):
        """
        Create a QR code.
        """
        qr_embed = discord.Embed()
        qr_embed.add_field(name="QR code", value=f"Here is your qr code ({content})")
        qr_embed.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?data={content}&size=250x250")
        await ctx.send(embed=qr_embed)

    @core.group(hybrid=True, fallback="get", case_insensitive=True, invoke_without_command=True)
    async def time(self, ctx: Context, *, member: discord.Member | None = None):
        """
        Get the time for a user.

        If the user does not have a timezone set up, an error will occur.
        """
        member = member or ctx.author
        user = ctx.database.get_user(ctx.author.id)
        if user and user.timezone:
            timezone = pytz.timezone(user.timezone)
            time = dt.datetime.now(timezone)
            format_time = time.strftime("%A, %B %d at %I:%M %p")
            time_embed = discord.Embed(description=format_time)
            time_embed.set_author(name=f"{member.display_name}'s time", icon_url=member.display_avatar.url)
            time_embed.set_footer(text=f"{member.display_name}'s' timezone: {timezone}")
            return await ctx.send(embed=time_embed)
        message = f"{member} doesn't have a timezone set up."
        if member == ctx.author:
            message = "Use `{ctx.clean_prefix}time set <timezone>` to add your timezone."
        return await ctx.send(message)

    @time.command(name="set")
    async def time_set(self, ctx: Context, *, timezone: str):
        """
        Set your timezone.

        The timezone must be one of [these timezones.](https://gist.github.com/Soheab/3bec6dd6c1e90962ef46b8545823820d)
        """
        user_settings = await ctx.database.get_or_fetch_user(ctx.author.id)
        if timezone.lower() in ["remove", "none"]:
            await user_settings.update(timezone=None)
            return await ctx.send("Deleted your timezone.")
        try:
            timezones = pytz.timezone(timezone)
        except KeyError as e:
            raise TimeZoneError(timezone) from e
        await user_settings.update(timezone=timezone)
        return await ctx.send(f"Set timezone to {timezones}")

    @core.command()
    @core.cooldown(1, 15, commands.BucketType.guild)
    async def firstmessage(
        self, ctx: Context, *, channel: discord.TextChannel | discord.VoiceChannel | discord.Thread | None = None
    ):
        """
        Get the first message of the channel.

        This will give you the jump url of the message.
        """
        if channel is None:
            channel = ctx.channel
        messages = [message async for message in channel.history(limit=1, oldest_first=True)]
        if len(messages[0].content) > 100:
            mg_cnt = messages[0].content[:100]
        mg_cnt = messages[0].content
        embed_message = discord.Embed(
            title=f"First Message of #{channel.name}",
            description=f"Here is the message link. [jump]({messages[0].jump_url})\n\n>>> {mg_cnt}",
        )
        await ctx.send(embed=embed_message)

    @core.group(
        hybrid=True,
        fallback="discord-py",
        aliases=["rtfm", "rtfd", "documentation"],
        invoke_without_command=True,
    )
    @core.describe(query="What to search for.")
    async def docs(self, ctx: Context, query: str):
        """
        Get the docs for the discord.py library.
        """
        q = await self.scraper.search(query, page="https://discordpy.readthedocs.io/en/latest/")
        if not q:
            return await ctx.send("No results found.")
        menu = Paginator(RTFMPageSource(ctx, q[:79], "Discord.py"), ctx=ctx, remove_view_after=True)
        return await menu.start()

    @docs.command(aliases=["py"])
    @core.describe(query="What to search for.")
    async def python(self, ctx: Context, *, query: str):
        """
        Get the docs for the latest Python version
        """
        q = await self.scraper.search(query, page="https://docs.python.org/3/")
        if not q:
            return await ctx.send("No results found.")
        menu = Paginator(RTFMPageSource(ctx, q[:79], "Python"), ctx=ctx, remove_view_after=True)
        return await menu.start()

    @docs.command(aliases=["wl"])
    @core.describe(query="What to search for.")
    async def wavelink(self, ctx: Context, query: str):
        """
        Get the docs for the Wavelink library
        """
        q = await self.scraper.search(query, page="https://wavelink.readthedocs.io/en/latest/")
        if not q:
            return await ctx.send("No results found.")
        menu = Paginator(RTFMPageSource(ctx, q[:79], "Wavelink"), ctx=ctx, remove_view_after=True)
        return await menu.start()

    @docs.command(aliases=["c"])
    @core.describe(url="The URL to search docs for.", query="What to search for.")
    async def custom(self, ctx: Context, url: str, *, query: str):
        """
        Search any Sphinx docs.
        """
        try:
            q = await self.scraper.search(query, page=url)
        except Exception as e:
            return await ctx.send(str(e))
        if not q:
            return await ctx.send("No results found.")
        menu = Paginator(RTFMPageSource(ctx, q[:79], "Custom Docs"), ctx=ctx, remove_view_after=True)
        return await menu.start()

    @core.group(name="gist", invoke_without_command=True)
    @core.cooldown(1, 60, commands.BucketType.user)
    async def gist(self, ctx: Context, *, code: codeblock_converter):  # type: ignore
        """
        Posts a gist.

        These gists are public and if you want to get one removed, DM Alpine or join the support server.
        """
        file_post = asyncgist.File(filename=f"output.{code.language or 'txt'}", content=code.content)
        out = await self.bot.gist.post_gist(
            description=f"{ctx.author} at {dt.datetime.now(dt.timezone.utc).strftime('%x %X')}",
            files=[file_post],
            public=True,
        )
        await ctx.send(f"These gists are posted publicly. DM me to get it removed.\n{out.html_url}")

    @gist.command(name="delete")
    @core.is_owner()
    async def gist_delete(self, ctx, *, gist_id: str):
        """
        Deletes a gist

        This deletes gists posted from the alpine-bot GitHub account.
        """
        try:
            await self.bot.gist.delete_gist(gist_id)
        except asyncgist.NotFound:
            return await ctx.send("Gist was not found.")
        return await ctx.send("Deleted post.")

    @gist.command(name="read")
    async def gist_read(self, ctx, *, gist_id: str):
        try:
            gist = await self.bot.gist.fetch_gist(gist_id)
        except asyncgist.NotFound:
            return await ctx.send("Gist was not found.")
        from core.context import AutoPageSource

        pag = commands.Paginator()
        for i in gist.files[0].content.split("\n"):  # type: ignore
            pag.add_line(i.replace("`", "\u200b`"))
        source = AutoPageSource(pag)
        pages = Paginator(source, ctx=ctx, delete_message_after=True)
        return await pages.start()

    @core.command(aliases=["rawmsg", "rmessage", "rmsg"])
    @core.cooldown(1, 15, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def rawmessage(self, ctx: Context, message_id: int | None = None):
        """
        Get the raw content of a message.

        If the message is too long, it will be posted on a gist.
        """
        ref = ctx.reference
        if message_id is None and ref is not None:
            message_id = ref.id
        if not ref and message_id is None:
            return await ctx.send("Provide a message id or reply to a message using this command.")
        assert message_id is not None
        mess = await self.bot.http.get_message(ctx.channel.id, message_id)
        dumps = json.dumps(mess, indent=4)
        info = ctx.codeblock(dumps, language="json")
        if len(info) > 2000:
            info = f"The output was too long, posted to {await ctx.post(content=dumps, filename='raw_message.json')}"
        return await ctx.send(info)
