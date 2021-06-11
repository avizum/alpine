"""
Settings for the bot itself.
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

import asyncio
import discord

from discord.ext import commands
from utils import AvimetryBot, AvimetryContext, Prefix, preview_message


class Settings(commands.Cog):
    """
    Configure bot settings.
    """
    def __init__(self, avi):
        self.avi: AvimetryBot = avi
        self.map = {
            True: "Enabled",
            False: "Disabled"}

    @commands.group(
        brief="Configure the server's prefixes",
        case_insensitive=True,
        invoke_without_command=True)
    async def prefix(self, ctx: AvimetryContext):
        prefix = await ctx.cache.get_guild_settings(ctx.guild.id)
        if not prefix["prefixes"]:
            return await ctx.send("This server doesn't have a custom prefix set yet. The default prefix is always `a.`")
        else:
            guild_prefix = prefix["prefixes"]
        if len(guild_prefix) == 1:
            return await ctx.send(f"The prefix for this server is `{guild_prefix[0]}`")
        await ctx.send(f"Here are my prefixes for this server: \n`{'` | `'.join(guild_prefix)}`")

    @prefix.command(
        name="add",
        brief="Add a prefix to the server"
    )
    @commands.has_permissions(manage_guild=True)
    async def prefix_add(self, ctx: AvimetryContext, prefix: Prefix):
        query = "UPDATE guild_settings SET prefixes = ARRAY_APPEND(prefixes, $2) WHERE guild_id = $1"
        await self.avi.pool.execute(query, ctx.guild.id, prefix)
        ctx.cache.guild_settings[ctx.guild.id]["prefixes"].append(prefix)
        await ctx.send(f"Appended `{prefix}` to the list of prefixes.")

    @prefix.command(
        name="remove",
        brief="Remove a prefix from the server"
    )
    @commands.has_permissions(manage_guild=True)
    async def prefix_remove(self, ctx: AvimetryContext, prefix):
        prefix = prefix.lower()
        guild_cache = await ctx.cache.get_guild_settings(ctx.guild.id)
        if not guild_cache:
            return await ctx.send(
                "You don't have any prefixes set for this server. Set one by using `a.settings prefix add <prefix>`")

        guild_prefix = guild_cache["prefixes"]
        if prefix not in guild_prefix:
            return await ctx.send(f"`{prefix}` is not a prefix of this server.")

        query = "UPDATE guild_settings SET prefixes = ARRAY_REMOVE(prefixes, $2) WHERE guild_id = $1"
        await self.avi.pool.execute(query, ctx.guild.id, prefix)

        self.avi.cache.guild_settings[ctx.guild.id]["prefixes"].remove(prefix)
        await ctx.send(f"Removed `{prefix}` from the list of prefixes")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def muterole(self, ctx: AvimetryContext, role: discord.Role):
        query = "UPDATE guild_settings SET mute_role = $1 WHERE guild_id = $2"
        await self.avi.pool.execute(query, role.id, ctx.guild.id)
        self.avi.cache.guild_settings[ctx.guild.id]["mute_role"] = role.id
        for channel in ctx.guild.channels:
            perms = channel.overwrites_for(role)
            perms.update(send_messages=False)
            await channel.set_permissions(
                target=role,
                overwrite=perms,
                reason=f"Mute role set to {role.name} by {ctx.author}"
            )
        await ctx.send(f"Set the mute role to {role.mention}")

    @commands.group(invoke_without_command=True, brief="Configure logging")
    @commands.has_permissions(manage_guild=True)
    async def logging(self, ctx: AvimetryContext, toggle: bool = None):
        if toggle is None:
            config = ctx.cache.logging[ctx.guild.id]
            embed = discord.Embed(
                title="Logging Configuation",
                description=(
                    "```py\n"
                    f"Global Toggle: {self.map[config['enabled']]}\n"
                    f"Logging Channel ID: {config['channel_id']}\n"
                    f"Message Delete: {config['message_delete']}\n"
                    f"Message Edit: {config['message_edit']}```"))
            return await ctx.send(embed=embed)
        query = "UPDATE logging SET enabled = $1 WHERE guild_id = $2"
        await self.avi.pool.execute(query, toggle, ctx.guild.id)
        ctx.cache.logging[ctx.guild.id]["enabled"] = toggle
        await ctx.send(f"{self.map[toggle]} logging")

    @logging.command(name="channel", brief="Configure logging channel")
    @commands.has_permissions(manage_guild=True)
    async def logging_channel(self, ctx: AvimetryContext, channel: discord.TextChannel):
        query = "UPDATE logging SET channel_id = $1 WHERE guild_id = $2"
        await self.avi.pool.execute(query, channel.id, ctx.guild.id)
        ctx.cache.logging[ctx.guild.id]["channel_id"] = channel.id

    @logging.command(
        brief="Configure delete logging",
        name="message_delete",
        aliases=["msgdelete, messagedelete"])
    @commands.has_permissions(manage_guild=True)
    async def message_delete(self, ctx: AvimetryContext, toggle: bool):
        query = "UPDATE logging SET message_delete = $1 WHERE guild_id = $2"
        await self.avi.pool.execute(query, toggle, ctx.guild.id)
        ctx.cache.logging[ctx.guild.id]["message_delete"] = toggle
        await ctx.send(f"{self.map[toggle]} message delete logs")

    @logging.command(
        brief="Configure edit logging",
        name="message_edit",
        aliases=["msgedit", "messageedit"])
    @commands.has_permissions(administrator=True)
    async def edit(self, ctx: AvimetryContext, toggle: bool):
        query = "UPDATE logging SET message_edit = $1 WHERE guild_id = $2"
        await self.avi.pool.execute(query, toggle, ctx.guild.id)
        ctx.cache.logging[ctx.guild.id]["message_edit"] = toggle
        await ctx.send(f"{self.map[toggle]} message edit logs")

    @commands.group(
        name="join-message",
        invoke_without_command=True
        )
    @commands.has_permissions(manage_guild=True)
    async def join_message(self, ctx: AvimetryContext, toggle: bool = None):
        if toggle is None:
            try:
                config = ctx.cache.join_leave.get(ctx.guild.id)
                join_message = config["join_message"]
                embed = discord.Embed(
                    title="Join Message Configuration",
                    description=(
                        "```py\n"
                        f"Toggle: {self.map[config['join_enabled']]}\n"
                        f"Join Message: {join_message if len(join_message) < 10 else 'Too Long.'}\n"
                        f"Join Channel ID: {config['join_channel']}```"))
                return await ctx.send(embed=embed)
            except KeyError:
                embed = discord.Embed(
                    title="Join Message Configutation",
                    description=(
                        "You do not have join messages setup yet.\n"
                        "Do you want to set them up?"
                    )
                )
                confirm = await ctx.confirm(embed=embed)
                if confirm:
                    command = self.avi.get_command("join-message setup")
                    await command(ctx)
                return
        query = (
            """
            INSERT INTO join_leave (guild_id, join_enabled)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET join_enabled = $2
            """
        )
        await self.avi.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.join_leave[ctx.guild.id]["join_enabled"] = toggle
        await ctx.send(f"{self.map[toggle]} join message")

    @join_message.command(
        name="set",
        brief="Set the message when a member joins"
    )
    @commands.has_permissions(manage_guild=True)
    async def join_message_set(self, ctx: AvimetryContext, *, message: str):
        conf_message = "Does this look good to you?"
        thing = await preview_message(message, ctx)
        if type(thing) == discord.Embed:
            conf = await ctx.confirm(conf_message, embed=thing, raw=True)
        else:
            conf = await ctx.confirm(f"{conf_message}\n\n{thing}", raw=True)
        if conf:
            query = (
                """
                INSERT INTO join_leave (guild_id, join_message)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO
                UPDATE SET join_message = $2
                """
            )
            await self.avi.pool.execute(query, ctx.guild.id, message)
            ctx.cache.join_leave[ctx.guild.id]["join_message"] = message
            return await ctx.send("Succesfully set the join message.")
        return await ctx.send("Cancelled")

    @join_message.command(
        name="channel",
        brief="Set the join message channel"
    )
    @commands.has_permissions(manage_guild=True)
    async def join_message_channel(self, ctx: AvimetryContext, channel: discord.TextChannel):
        query = (
            """
            INSERT INTO join_leave (guild_id, join_channel)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET join_channel = $2
            """
        )
        await self.avi.pool.execute(query, channel.id, ctx.guild.id)
        ctx.cache.join_leave[ctx.guild.id]["join_channel"] = channel.id
        await ctx.send(f"Set the join message channel to {channel.mention}")

    @join_message.command(
        name="setup",
        brief="Setup join message"
    )
    @commands.has_permissions(manage_guild=True)
    async def join_message_setup(self, ctx: AvimetryContext):
        embed = discord.Embed(
            title="Join message setup",
            description="Hello. Which channel would you like to send the join messages to?"
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author
        try:
            wait_channel = await self.avi.wait_for("message", check=check, timeout=300)
        except asyncio.TimeoutError:
            embed.description = "Cancelling due to timeout."
            await ctx.send(embed=embed)
        else:
            if wait_channel.content.lower() == "cancel":
                embed.description = "Okay, I cancelled the setup, Goodbye."
                return await wait_channel.reply(embed=embed)
            try:
                channel = await commands.TextChannelConverter().convert(ctx, wait_channel.content)
            except commands.ChannelNotFound:
                embed.description = "That is not a channel. Goodbye."
                return await wait_channel.reply(embed=embed)
            if channel:
                embed.description = (
                    f"Okay, the channel will be {channel.mention}.\n"
                    "What should the join message be? (5 minutes)")
                await wait_channel.reply(embed=embed)
        try:
            wait_message = await self.avi.wait_for("message", check=check, timeout=300)
        except asyncio.TimeoutError:
            embed.description = "Cancelling due to timeout."
            return await ctx.send(embed=embed)
        else:
            if wait_channel.content.lower() == "cancel":
                embed.description = "Okay, I cancelled the setup, Goodbye."
            message = wait_message.content
            conf_message = "Does this look good to you?"
            preview = await preview_message(message, ctx)
            if type(preview) == discord.Embed:
                conf = await ctx.confirm(conf_message, embed=preview, raw=True)
            else:
                conf = await ctx.confirm(f"{conf_message}\n=====\n{preview}", raw=True)
            if conf:
                query = (
                    """
                    INSERT INTO join_leave (guild_id, join_enabled, join_message, join_channel)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (guild_id) DO
                    UPDATE SET guild_id = $1, join_enabled = $2, join_message = $3, join_channel = $4
                    """
                )
                await self.avi.pool.execute(query, ctx.guild.id, True, message, channel.id)
                ctx.cache.join_leave[ctx.guild.id]["join_enabled"] = True
                ctx.cache.join_leave[ctx.guild.id]["join_message"] = message
                ctx.cache.join_leave[ctx.guild.id]["join_channel"] = channel.id
                embed.description = "Alright, join messages are now setup."
                return await wait_message.reply(embed=embed)
            embed.description = "Cancelled. Goodbye."
            return await wait_message.reply(embed=embed)

    @commands.group(
        name="leave-message",
        invoke_without_command=True
        )
    @commands.has_permissions(manage_guild=True)
    async def leave_message(self, ctx: AvimetryContext, toggle: bool = None):
        if toggle is None:
            try:
                config = ctx.cache.join_leave.get(ctx.guild.id)
                join_message = config["leave_message"]
                embed = discord.Embed(
                    title="Leave Message Configuration",
                    description=(
                        "```py\n"
                        f"Toggle: {self.map[config['leave_enabled']]}\n"
                        f"Join Message: {join_message if len(join_message) < 10 else 'Too Long.'}\n"
                        f"Join Channel ID: {config['leave_channel']}```"))
                return await ctx.send(embed=embed)
            except KeyError:
                embed = discord.Embed(
                    title="Leave Message Configuration",
                    description=(
                        "You do not have leave messages setup yet.\n"
                        "Do you want to set them up?"
                    )
                )
                confirm = await ctx.confirm(embed=embed)
                if confirm:
                    command = self.avi.get_command("leave-message setup")
                    await command(ctx)
                return
        query = "UPDATE join_leave SET leave_enabled = $1 WHERE guild_id = $2"
        await self.avi.pool.execute(query, toggle, ctx.guild.id)
        ctx.cache.join_leave[ctx.guild.id]["leave_enabled"] = toggle
        await ctx.send(f"{self.map[toggle]} leave message")

    @leave_message.command(
        name="set",
        brief="Set the message when a member leaves"
    )
    @commands.has_permissions(manage_guild=True)
    async def leave_message_set(self, ctx: AvimetryContext, *, message: str):
        conf_message = "Does this look good to you?"
        thing = await preview_message(message, ctx)
        if type(thing) == discord.Embed:
            conf = await ctx.confirm(conf_message, embed=thing, raw=True)
        else:
            conf = await ctx.confirm(f"{conf_message}\n\n{thing}", raw=True)
        if conf:
            query = (
                """
                INSERT INTO join_leave (guild_id, leave_message)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO
                UPDATE SET leave_message = $2
                """
            )
            await self.avi.pool.execute(query, ctx.guild.id, message)
            ctx.cache.join_leave[ctx.guild.id]["leave_message"] = message
            return await ctx.send("Succesfully set leave message.")
        return await ctx.send("Aborted set leave message.")

    @leave_message.command(
        name="channel",
        brief="Set the leave message channel"
    )
    @commands.has_permissions(manage_guild=True)
    async def leave_message_channel(self, ctx: AvimetryContext, channel: discord.TextChannel):
        query = (
            """
            INSERT INTO join_leave (guild_id, join_channel)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET join_channel = $2
            """
        )
        await self.avi.pool.execute(query, channel.id, ctx.guild.id)
        ctx.cache.join_leave[ctx.guild.id]["leave_channel"] = channel.id
        await ctx.send(f"Set the leave message channel to {channel.mention}")

    @leave_message.command(
        name="setup",
        brief="Setup leave messages"
    )
    @commands.has_permissions(manage_guild=True)
    async def leave_message_setup(self, ctx: AvimetryContext):
        embed = discord.Embed(
            title="Leave message setup",
            description="Hello. Which channel would you like to send the leave messages to?"
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author
        try:
            wait_channel = await self.avi.wait_for("message", check=check, timeout=300)
        except asyncio.TimeoutError:
            embed.description = "Cancelling due to timeout."
            await ctx.send(embed=embed)
        else:
            if wait_channel.content.lower() == "cancel":
                embed.description = "Okay, I cancelled the setup, Goodbye."
                return await wait_channel.reply(embed=embed)
            try:
                channel = await commands.TextChannelConverter().convert(ctx, wait_channel.content)
            except commands.ChannelNotFound:
                embed.description = "That is not a channel. Goodbye."
                return await wait_channel.reply(embed=embed)
            if channel:
                embed.description = (
                    f"Okay, the channel will be {channel.mention}.\n"
                    "What should the leave message be? (5 minutes)")
                await wait_channel.reply(embed=embed)
        try:
            wait_message = await self.avi.wait_for("message", check=check, timeout=300)
        except asyncio.TimeoutError:
            embed.description = "Cancelling due to timeout."
            return await ctx.send(embed=embed)
        else:
            if wait_channel.content.lower() == "cancel":
                embed.description = "Okay, I cancelled the setup, Goodbye."
            message = wait_message.content
            conf_message = "Does this look good to you?"
            preview = await preview_message(message, ctx)
            if type(preview) == discord.Embed:
                conf = await ctx.confirm(conf_message, embed=preview, raw=True)
            else:
                conf = await ctx.confirm(f"{conf_message}\n=====\n{preview}", raw=True)
            if conf:
                query = (
                    """
                    INSERT INTO join_leave (guild_id, leave_enabled, leave_message, leave_channel)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (guild_id) DO
                    UPDATE SET guild_id = $1, leave_enabled = $2, leave_message = $3, leave_channel = $4
                    """
                )
                await self.avi.pool.execute(query, ctx.guild.id, True, message, channel.id)
                ctx.cache.join_leave[ctx.guild.id]["leave_enabled"] = True
                ctx.cache.join_leave[ctx.guild.id]["leave_message"] = message
                ctx.cache.join_leave[ctx.guild.id]["leave_channel"] = channel.id
                embed.description = "Alright, leave messages are now setup."
                return await wait_message.reply(embed=embed)
            embed.description = "Cancelled. Goodbye."
            return await wait_message.reply(embed=embed)

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    async def screening(self, ctx: AvimetryContext, toggle: bool = None):
        if toggle is None:
            embed = discord.Embed(description=(
                f"Role: {ctx.cache.verification[ctx.guild.id]['high']}\n"
                f"Toggle: {ctx.cache.verification[ctx.guild.id]['role_id']}"
                )
            )
            return await ctx.send(embed=embed)
        query = (
            """
            INSERT INTO verification (guild_id, high)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET guild_id = $1, high = $2
            """
        )
        await self.avi.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.verification[ctx.guild.id]["high"] = toggle
        return await ctx.send(f"{self.map[toggle]} member screening")

    @screening.command(name="role")
    @commands.has_permissions(manage_guild=True)
    async def screening_role(self, ctx: AvimetryContext, role: discord.Role):
        query = (
            """
            INSERT INTO VERIFICATION (guild_id, role_id)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET role_id = $2
            """
        )
        await self.avi.pool.execute(query, ctx.guild.id, role.id)
        ctx.cache.verifiction[ctx.guild.id]["role_id"] = role.id
        return await ctx.send(f"Set screening role to `{role.mention}.`")


def setup(avi):
    avi.add_cog(Settings(avi))
