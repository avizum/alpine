"""
[Avimetry Bot]
Copyright (C) 2021 - 2022 avizum

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

import datetime
import json
import random

import aiohttp
import asyncgist
import discord
import pytz
from doc_search import AsyncScraper
from discord.ext import commands, menus
from discord.utils import format_dt
from jishaku.codeblocks import codeblock_converter
from pytz import UnknownTimeZoneError

import core
from core import Bot, Context
from utils import Paginator, PaginatorEmbed, Emojis


class TimeZoneError(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__(
            f'Timezone "{argument}" was not found. [Here]'
            "(https://gist.github.com/Soheab/3bec6dd6c1e90962ef46b8545823820d) "
            "are all the valid timezones you can use."
        )


class RTFMPageSource(menus.ListPageSource):
    def __init__(self, ctx: Context, items, query):
        super().__init__(items, per_page=12)
        self.ctx = ctx
        self.items = items
        self.query = query

    async def format_page(self, menu, page):
        embed = PaginatorEmbed(
            ctx=self.ctx,
            description=(
                "\n".join(f"[`{k.replace('discord.', '').replace('discord.ext.commands.', '')}`]({v})" for k, v in page)
            ),
        )
        embed.set_footer(text=f"{len(self.items)} results found")
        return embed


class Meta(core.Cog):
    """
    Extra commands that do not lie in any category.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.scraper = AsyncScraper(self.bot.loop, self.bot.session)

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
            description += "\n\n{} {}".format(reactions[x], option)
        embed = discord.Embed(title=question, description="".join(description))
        react_message = await ctx.channel.send(embed=embed)
        for reaction in reactions[: len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(text=f"Poll from: {ctx.author}\nMessage ID: {react_message.id}")

        await react_message.edit(embed=embed)

    @core.command()
    @core.cooldown(1, 1, commands.BucketType.member)
    async def pick(self, ctx: Context, *, options):
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
    async def userinfo(self, ctx: Context, *, member: discord.Member | discord.User = commands.Author):
        """
        Get info about a user.

        This works with any user on Discord.
        """
        if isinstance(member, discord.User):
            ie = discord.Embed(
                title="User Information",
                description="This user in not in this server",
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                color=member.color,
            )
            ie.add_field(name="User Name", value=str(member))
            ie.add_field(name="User ID", value=member.id)
            ie.add_field(
                name="Creation Date",
                value=f"{format_dt(member.created_at)} ({format_dt(member.created_at, 'R')})",
                inline=False,
            )
        else:
            if ctx.interaction:
                member = ctx.guild.get_member(member.id)
            userroles = ["@everyone"]
            userroles.extend(roles.mention for roles in member.roles)
            userroles.remove(ctx.guild.default_role.mention)
            ie = discord.Embed(
                title="Member Information",
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                color=member.color,
            )
            ie.add_field(name="User Name", value=str(member))
            ie.add_field(name="User ID", value=member.id)
            if member.nick:
                ie.add_field(name="Nickname", value=member.nick)

            sort = sorted(ctx.guild.members, key=lambda m: m.joined_at)
            pos = f"{sort.index(member) + 1:,}/{len(ctx.guild.members):,}"
            ie.add_field(
                name="Join Date",
                value=f"{format_dt(member.joined_at)} ({format_dt(member.joined_at, 'R')})\nJoin Position: {pos}",
                inline=False,
            )
            ie.add_field(
                name="Account Creation Date",
                value=f"{format_dt(member.created_at)} ({format_dt(member.created_at, 'R')})",
                inline=False,
            )
            top_role = member.top_role.mention
            if top_role != ctx.guild.default_role.mention:
                ie.add_field(name="Top Role", value=top_role, inline=False)
            userroles = ", ".join(userroles)
            if len(userroles) > 1024:
                userroles = f"{member.display_name} has too many roles to show here."
            ie.add_field(
                name=f"Roles [{len(member.roles)}]",
                value=userroles,
                inline=False,
            )
            if member.public_flags.value > 0:
                flags = []
                for flag, value in member.public_flags:
                    new = flag.replace(flag, Emojis.BADGES.get(flag, flag))
                    if value is True:
                        if new == flag:
                            flags.append(flag.replace("_", " ").title())
                            continue
                        flags.append(f"{new} | {flag.replace('_', ' ').title()}")
                ie.add_field(name=f"Badges [{len(flags)}]", value=", ".join(flags))
            if member.status:
                desktop = member.desktop_status.name
                mobile = member.mobile_status.name
                web = member.web_status.name
                ie.add_field(
                    name="Status",
                    value=(
                        f"Desktop: {Emojis.STATUSES.get(desktop)} | {desktop.title()}\n"
                        f"Mobile: {Emojis.STATUSES.get(mobile)} | {mobile.title()}\n"
                        f"Web: {Emojis.STATUSES.get(web)} | {web.title()}"
                    ),
                    inline=False
                )

        ie.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=ie)

    @core.command()
    @core.is_owner()
    async def roleinfo(self, ctx: Context, role: discord.Role):
        embed = discord.Embed(title="Role Info")
        embed.add_field(name="Created At", value=discord.utils.format_dt(role.created_at))
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
    async def avatar(self, ctx: Context, member: discord.Member = None):
        """
        Sends the avatar of a member.
        """
        member = member or ctx.author
        embed = discord.Embed(
            title=f"{member}'s avatar",
            description=(
                f"[`png`]({member.display_avatar.with_static_format('png')}) | "
                f"[`jpg`]({member.display_avatar.with_static_format('jpg')}) | "
                f"[`webp`]({member.display_avatar.url})"
            ),
        )
        avatar = member.avatar.url or member.default_avatar.url
        embed.set_image(url=avatar)
        if member.guild_avatar:
            embed.set_thumbnail(url=member.guild_avatar.url)
        await ctx.send(embed=embed)

    @core.command()
    @core.cooldown(2, 10, commands.BucketType.guild)
    async def banner(self, ctx: Context, member: discord.Member | discord.User = None):
        """
        Send the banner of a member.

        If they have no banner and have an accent color, it will send the accent color instead.
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
        await ctx.send(embed=embed)

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
    async def time(self, ctx: Context, *, member: discord.Member = None):
        """
        Get the time for a user.

        If the user does not have a timezone set up, an error will occur.
        """
        member = member or ctx.author
        try:
            timezone = ctx.cache.users[member.id]["timezone"]
            if not timezone:
                raise KeyError
        except (KeyError, UnknownTimeZoneError):
            prefix = ctx.clean_prefix
            if member == ctx.author:
                return await ctx.send(f"You don't have a timezone setup yet. Use {prefix}time set <timezone>.")
            return await ctx.send(f"This user does not have a timezone setup. Use {prefix}time set <timezone>.")
        timezone = pytz.timezone(timezone)
        time = datetime.datetime.now(timezone)
        format_time = time.strftime("%A, %B %d at %I:%M %p")
        time_embed = discord.Embed(description=format_time)
        time_embed.set_author(name=f"{member.display_name}'s time", icon_url=member.display_avatar.url)
        time_embed.set_footer(text=f"{member.display_name}'s' timezone: {timezone}")
        await ctx.send(embed=time_embed)

    @time.command(name="set")
    async def time_set(self, ctx: Context, *, timezone):
        """
        Set your timezone.

        The timezone must be one of [these timezones.](https://gist.github.com/Soheab/3bec6dd6c1e90962ef46b8545823820d)
        """
        query = (
            "INSERT INTO user_settings (user_id, timezone) "
            "VALUES ($1, $2) "
            "ON CONFLICT (user_id) DO "
            "UPDATE SET timezone = $2"
        )
        if timezone.lower() in ["remove", "none"]:
            await self.bot.pool.execute(query, ctx.author.id, None)
            try:
                ctx.cache.users[ctx.author.id]["timezone"] = timezone
            except KeyError:
                new = await ctx.cache.new_user(ctx.author.id)
                new["timezone"] = timezone
            return await ctx.send("Remove timezone")
        try:
            timezones = pytz.timezone(timezone)
        except KeyError as e:
            raise TimeZoneError(timezone) from e
        await self.bot.pool.execute(query, ctx.author.id, timezone)
        try:
            ctx.cache.users[ctx.author.id]["timezone"] = timezone
        except KeyError:
            new = await ctx.cache.new_user(ctx.author.id)
            new["timezone"] = timezone
        await ctx.send(f"Set timezone to {timezones}")

    @core.command()
    @core.cooldown(1, 15, commands.BucketType.guild)
    async def firstmessage(self, ctx: Context, *, channel: discord.TextChannel = None):
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
        aliases=["rtfd", "rtm", "rtd", "docs"],
        invoke_without_command=True,
    )
    async def rtfm(self, ctx: Context, query):
        """
        Get the docs for the discord.py library.
        """
        q = await self.scraper.search(query, page="https://discordpy.readthedocs.io/en/stable/")
        menu = Paginator(RTFMPageSource(ctx, q[:79], "Discord.py"), ctx=ctx, remove_view_after=True)
        await menu.start()

    @rtfm.command()
    async def master(self, ctx: Context, query):
        """
        Get the docs for the discord.py master branch library.
        """
        q = await self.scraper.search(query, page="https://discordpy.readthedocs.io/en/master/")
        menu = Paginator(
            RTFMPageSource(ctx, q[:79], "Discord.py 2.0"),
            ctx=ctx,
            remove_view_after=True,
        )
        await menu.start()

    @rtfm.command(aliases=["py"])
    async def python(self, ctx: Context, query):
        """
        Get the docs for the latest Python version
        """
        q = await self.scraper.search(query, page="https://docs.python.org/3/")
        menu = Paginator(RTFMPageSource(ctx, q[:79], "Python"), ctx=ctx, remove_view_after=True)
        await menu.start()

    @rtfm.command(aliases=["ob"])
    async def obsidian(self, ctx: Context, query):
        """
        Get the docs for the Obsidian.py library
        """
        q = await self.scraper.search(query, page="https://obsidianpy.readthedocs.io/en/latest/")
        menu = Paginator(RTFMPageSource(ctx, q[:79], "Obsidian"), ctx=ctx, remove_view_after=True)
        await menu.start()

    @rtfm.command(aliases=["wl"])
    async def wavelink(self, ctx: Context, query):
        """
        Get the docs for the Wavelink library
        """
        q = await self.scraper.search(query, page="https://wavelink.readthedocs.io/en/latest/")
        menu = Paginator(RTFMPageSource(ctx, q[:79], "Wavelink"), ctx=ctx, remove_view_after=True)
        await menu.start()

    @rtfm.command(aliases=["c"])
    async def custom(self, ctx: Context, doc_url, query):
        """
        Search any Sphinx docs.
        """
        try:
            q = await self.scraper.search(query, page=doc_url)
        except Exception as e:
            return await ctx.send(e)
        menu = Paginator(RTFMPageSource(ctx, q[:79], "Custom Docs"), ctx=ctx, remove_view_after=True)
        await menu.start()

    @core.command()
    @core.cooldown(1, 300, commands.BucketType.member)
    async def embed(self, ctx: Context, *, thing: str):
        """
        Make embeds with JSON.

        This command has a high cooldown to prevent abuse.
        """
        if '"content":' in thing:
            return await ctx.send('Remove the "content" part from your message and try again.')
        try:
            thing = json.loads(thing)
            return await ctx.no_reply(embed=discord.Embed.from_dict(thing))
        except Exception as e:
            embed = discord.Embed(
                title="Input Error",
                description=f"The JSON input raised an error:\n```bash\n{e}```",
            )
            return await ctx.no_reply(embed=embed)

    @core.command(enabled=False)
    async def redirectcheck(self, ctx: Context, url: str):
        """
        Check what a URL leads to.

        Useful to see if a link is a rickroll or something.
        """
        url = url.strip("<>")
        async with self.bot.session.get(url) as f:
            await ctx.no_reply(f"This url redirects to:\n\n{f.real_url}")

    @redirectcheck.error
    async def redirectcheck_error(self, ctx: Context, error):
        if isinstance(error, aiohttp.InvalidURL):
            return await ctx.send("This is not a valid url. Make sure you start links with `http://` or `https://`.")
        if isinstance(error, aiohttp.ClientConnectorError):
            return await ctx.send("I wasn't able to connect to this website.")
        await ctx.send("An error occured while checking the link, Please try another link or try again later.")
        raise error

    @core.group(name="gist", invoke_without_command=True)
    @core.cooldown(1, 60, commands.BucketType.user)
    async def gist(self, ctx: Context, *, code: codeblock_converter):
        """
        Posts a gist.

        These gists are public and if you want to get one removed, DM Avimetry or join the support server.
        """
        file_post = asyncgist.File(filename=f"output.{code.language or 'txt'}", content=code.content)
        out = await self.bot.gist.post_gist(
            description=f"{ctx.author} at {datetime.datetime.now(datetime.timezone.utc).strftime('%x %X')}",
            files=[file_post],
            public=True,
        )
        await ctx.send(f"These gists are posted publicly. DM me to get it removed.\n{out.html_url}")

    @gist.command(name="delete")
    @core.is_owner()
    async def gist_delete(self, ctx, *, gist_id: str):
        """
        Deletes a gist

        This deletes gists posted from the avimetry-bot GitHub account.
        """
        try:
            await self.bot.gist.delete_gist(gist_id)
        except asyncgist.NotFound:
            return await ctx.send("Gist was not found.")
        await ctx.send("Deleted post.")

    @gist.command(name="read")
    async def gist_read(self, ctx, *, gist_id: str):
        try:
            gist = await self.bot.gist.fetch_gist(gist_id)
        except asyncgist.NotFound:
            return await ctx.send("Gist was not found.")
        from core.context import AutoPageSource

        pag = commands.Paginator()
        for i in gist.files[0].content.split("\n"):
            pag.add_line(i.replace("`", "\u200b`"))
        source = AutoPageSource(pag)
        pages = Paginator(source, ctx=ctx, delete_message_after=True)
        await pages.start()

    @core.command(aliases=["rawmsg", "rmessage", "rmsg"])
    @core.cooldown(1, 15, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def rawmessage(self, ctx: Context, message_id: int = None):
        """
        Get the raw content of a message.

        If the message is too long, it will be posted on a gist.
        """
        ref = ctx.message.reference
        if not ref:
            return await ctx.send("Provide a message id or reply to a message using this command.")
        if message_id is None and isinstance(ref.resolved, discord.Message):
            message_id = ref.resolved.id
        mess = await self.bot.http.get_message(ctx.channel.id, message_id)
        info = ctx.codeblock(json.dumps(mess, indent=4), language="json")
        if len(info) > 2000:
            return await ctx.post(info.removeprefix("```json\n").removesuffix("```"), "json", gist=True)
        return await ctx.send(info)

    @core.command(hidden=True)
    @core.is_owner()
    async def _(self, ctx):
        """
        Congrats have a cookie! 🍪
        """
        return
