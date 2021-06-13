"""
Extra commands for users.
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

import json
import aiohttp
import discord
import datetime
import random
import humanize
import pytz
import typing

from discord.ext import commands
from utils import AvimetryBot, AvimetryContext, TimeZoneError, GetAvatar


class Meta(commands.Cog):
    """
    Extra commands that do not lie in any category.
    """
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    @commands.command(brief="Sends a poll in the current channel for people to vote to.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def poll(self, ctx: AvimetryContext, question, *options: str):
        if len(options) < 2:
            raise commands.BadArgument(
                "You need to have at least two options in the poll."
            )
        if len(options) > 10:
            raise commands.BadArgument("You can only have twenty options in a poll")
        if len(options) == 3 and options[0] == "yes" and options[1] == "maybe" and options[2] == "no":
            reactions = [
                self.avi.emoji_dictionary["green_tick"],
                self.avi.emoji_dictionary["gray_tick"],
                self.avi.emoji_dictionary["red_tick"]
            ]
        elif len(options) == 2 and options[0].lower() == "yes" and options[1].lower() == "no":
            reactions = [
                self.avi.emoji_dictionary["green_tick"],
                self.avi.emoji_dictionary["red_tick"]
            ]
        else:
            reactions = [
                "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣",
                "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟",
            ]
        description = []
        for x, option in enumerate(options):
            description += "\n\n{} {}".format(reactions[x], option)
        embed = discord.Embed(title=question, description="".join(description))
        embed.set_footer(text=f"Poll from: {str(ctx.author)}")
        if ctx.guild.id == 751490725555994716:
            embed.color = ctx.author.color
            channel = discord.utils.get(ctx.guild.channels, id=774075297142013972)
            react_message = await channel.send(embed=embed)
        else:
            react_message = await ctx.send(embed=embed)
        for reaction in reactions[: len(options)]:
            await react_message.add_reaction(reaction)
        embed.set_footer(
            text=f"Poll from: {str(ctx.author)}\nPoll ID: {react_message.id}"
        )
        await react_message.edit(embed=embed)

    @commands.command(brief="Pick one of your options")
    @commands.cooldown(1, 1, commands.BucketType.member)
    async def pick(self, ctx: AvimetryContext, *, options):
        opt = options.split("or")
        if len(opt) != 2:
            opt = options.split(",")

        return await ctx.send(random.choice(opt))

    @commands.command(
        brief="Gets a member's information",
        aliases=["uinfo", "whois"]
    )
    async def userinfo(self, ctx: AvimetryContext, *, member: typing.Union[discord.Member, discord.User] = None):
        if member is None:
            member = ctx.author
        if isinstance(member, discord.User):
            ie = discord.Embed(
                title="User Information",
                description="This user in not in this server",
                timestamp=datetime.datetime.utcnow(),
                color=member.color,
            )
            ie.add_field(name="User Name", value=str(member))
            ie.add_field(name="User ID", value=member.id)
            ie.add_field(
                name="Creation Date",
                value=f"{humanize.naturaldate(member.created_at)} ({humanize.naturaltime(member.created_at)})",
                inline=False,
            )
        else:
            userroles = ["@everyone"]
            for roles in member.roles:
                userroles.append(roles.mention)
            userroles.remove(ctx.guild.default_role.mention)
            ie = discord.Embed(
                title="User Information",
                timestamp=datetime.datetime.utcnow(),
                color=member.color,
            )
            ie.add_field(name="User Name", value=str(member))
            ie.add_field(name="User ID", value=member.id)
            if member.nick:
                ie.add_field(name="Nickname", value=member.nick)
            ie.add_field(
                name="Join Date",
                value=f"{humanize.naturaldate(member.joined_at)} ({humanize.naturaltime(member.joined_at)})",
                inline=False,
            )
            ie.add_field(
                name="Account Creation Date",
                value=f"{humanize.naturaldate(member.created_at)} ({humanize.naturaltime(member.created_at)})",
                inline=False,
            )
            ie.add_field(name="Shared Servers", value=len(member.mutual_guilds))
            top_role = member.top_role.mention
            if top_role == ctx.guild.default_role.mention:
                top_role = "@everyone"
            userroles = ", ".join(userroles)
            if len(userroles) > 1024:
                userroles = f"{str(member.display_name)} has too many roles to show here."
            ie.add_field(name="Top Role", value=top_role, inline=False)
            ie.add_field(
                name=f"Roles [{len(member.roles)}]",
                value=userroles,
                inline=False,
            )
            if member.public_flags.value > 0:
                flags = [
                    key.replace("_", " ").title()
                    for key, val in member.public_flags
                    if val is True
                ]
                ie.add_field(name="Public Flags", value=", ".join(flags))
        ie.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=ie)

    @commands.command()
    async def avatar(self, ctx: AvimetryContext, member: discord.Member = None):
        if member is None:
            member = ctx.author
        embed = discord.Embed(
            title=f"{member}'s avatar"
        )
        embed.set_image(url=str(member.avatar_url))
        await ctx.send(embed=embed)

    @commands.group(brief="Make a QR code", invoke_without_command=True)
    async def qr(self, ctx: AvimetryContext, *, content):
        qr_embed = discord.Embed()
        qr_embed.add_field(name="QR code", value=f"Here is your qr code ({content})")
        qr_embed.set_image(
            url=f"https://api.qrserver.com/v1/create-qr-code/?data={content}&size=250x250"
        )
        await ctx.send(embed=qr_embed)

    @qr.command(brief="Read a QR code")
    async def read(self, ctx: AvimetryContext, *, image: GetAvatar):
        async with self.avi.session.get(f"https://api.qrserver.com/v1/read-qr-code/?fileurl={image}") as resp:
            thing = await resp.json()
            await ctx.send((str(thing[0]["symbol"][0]["data"])))

    @commands.group(brief="Gets the time for a member", invoke_without_command=True)
    async def time(self, ctx: AvimetryContext, *, member: discord.Member = None):
        if member is None:
            member = ctx.author
        try:
            timezone = ctx.cache.users[member.id]["timezone"]
        except KeyError:
            return await ctx.send("This user does not have a timezone setup.")
        timezone = pytz.timezone(timezone)
        time = datetime.datetime.now(timezone)
        format_time = time.strftime("%A, %B %d at %I:%M %p")
        time_embed = discord.Embed(description=format_time)
        time_embed.set_author(
            name=f"{member.display_name}'s time", icon_url=member.avatar_url
        )
        time_embed.set_footer(text=f"{member.display_name}'s' timezone: {timezone}")
        await ctx.send(embed=time_embed)

    @time.command(
        name="set",
        brief="Sets your timezone"
        )
    async def _set(self, ctx: AvimetryContext, *, timezone):
        try:
            timezones = pytz.timezone(timezone)
        except KeyError:
            raise TimeZoneError(timezone)
        query = (
                "INSERT INTO user_settings (user_id, timezone) "
                "VALUES ($1, $2) "
                "ON CONFLICT (user_id) DO "
                "UPDATE SET timezone = $2"
        )
        await self.avi.pool.execute(query, ctx.author.id, timezone)
        try:
            ctx.cache.users[ctx.author.id]["timezone"] = timezone
        except KeyError:
            new = await ctx.cache.new_user(ctx.author.id)
            new["timezone"] = timezone
        await ctx.send(f"Set timezone to {timezones}")

    @commands.command(brief="Get the jump link for the channel that you mention")
    async def firstmessage(self, ctx: AvimetryContext, *, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel
        messages = await channel.history(limit=1, oldest_first=True).flatten()
        if len(messages[0].content) > 100:
            mg_cnt = messages[0].content[:100]
        mg_cnt = messages[0].content
        embed_message = discord.Embed(
            title=f"First Message of #{channel.name}",
            description=f"Here is the message link. [jump]({messages[0].jump_url})\n\n>>> {mg_cnt}",
        )
        await ctx.send(embed=embed_message)

    @commands.command(
        aliases=["rtfd", "rtm", "rtd", "docs"]
    )
    async def rtfm(self, ctx: AvimetryContext, query):
        if len(query) < 3:
            return await ctx.send("Your search query needs to be at least 3 characters.")
        params = {
            "query": query,
            "location": "https://discordpy.readthedocs.io/en/latest"
        }
        async with self.avi.session.get("https://idevision.net/api/public/rtfm", params=params) as resp:
            response = await resp.json()
        if not response["nodes"]:
            return await ctx.send("Nothing found. Sorry.")
        listed = []
        for word, link in response["nodes"].items():
            word = word.replace("discord.", "")
            listed.append(f"[`{word}`]({link})")
        embed = discord.Embed(description="\n".join(listed))
        await ctx.send(embed=embed)

    @commands.command(
        brief="Make embeds. This command is not for normal members because it can be abused.")
    @commands.cooldown(5, 300, commands.BucketType.member)
    async def embed(self, ctx: AvimetryContext, *, thing: str):
        if '"content":' in thing or "'content':" in thing:
            return await ctx.send('Remove the "content" part from your message and try again.')
        try:
            thing = json.loads(thing)
            return await ctx.send_raw(embed=discord.Embed.from_dict(thing))
        except Exception as e:
            embed = discord.Embed(
                title="Input Error",
                description=f"The JSON input raised an error:\n```bash\n{e}```")
            return await ctx.send_raw(embed=embed)

    @commands.command(
        brief="Check what website a url redirects to"
    )
    async def redirectcheck(self, ctx: AvimetryContext, url: str):
        url = url.strip("<>")
        async with self.avi.session.get(url) as f:
            await ctx.send_raw(f"This url redirects to:\n\n{f.real_url}")

    @redirectcheck.error
    async def redirectcheck_error(self, ctx: AvimetryContext, error):
        if isinstance(error, aiohttp.InvalidURL):
            return await ctx.send("This is not a valid url. Make sure you start links with `http://` or `https://`.")
        if isinstance(error, aiohttp.ClientConnectorError):
            return await ctx.send("I wasn't able to connect to this website.")
        await ctx.send("An error occured while checking the link, Please try another link or try again later.")
        raise error

    @commands.command(hidden=True)
    @commands.is_owner()
    async def _(self, ctx):
        return


def setup(avi):
    avi.add_cog(Meta(avi))
