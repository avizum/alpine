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

import asyncio
import datetime

import discord
from discord.ext import commands

import core
from .converters import Prefix, GetCommand
from core import Bot, Context
from utils import preview_message


class Settings(core.Cog):
    """
    Configure bot settings.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.emoji = "\U00002699"
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.map = {True: "Enabled", False: "Disabled", None: "Not Set"}

    @core.group(case_insensitive=True, invoke_without_command=True)
    async def prefix(self, ctx: Context):
        """
        Show custom prefix configuration.
        """
        prefix = ctx.cache.guild_settings.get(ctx.guild.id)
        if not prefix["prefixes"]:
            return await ctx.send("The default prefix is `a.`")
        guild_prefix = prefix["prefixes"]
        if len(guild_prefix) == 1:
            return await ctx.send(f"Hey {ctx.author}, the prefix for {ctx.guild.name} is `{guild_prefix[0]}`")
        await ctx.send(f"Hey {ctx.author}, here are the prefixes for {ctx.guild.name}:\n`{'` | `'.join(guild_prefix)}`")

    @prefix.command(name="add", aliases=["append"])
    @core.has_permissions(manage_guild=True)
    async def prefix_add(self, ctx: Context, prefix: Prefix):
        """
        Adds a prefix to the server.

        Setting one prefix will remove the default prefix. Add it back if you want.
        If you want the prefix to have a space make sure to wrap it in quotations.
        You can have up to 15 prefixes, each up to 20 characters.
        The prefix can not be a channel, role or member mention.
        """
        query = (
            "INSERT INTO guild_settings (guild_id, prefixes) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET prefixes=$2"
        )
        prefixes = ctx.cache.guild_settings[ctx.guild.id]["prefixes"]
        prefixes.append(prefix)
        await self.bot.pool.execute(query, ctx.guild.id, prefixes)
        embed = discord.Embed(title="Current Prefixes", description=f"Added `{prefix}` to the list of prefixes.")
        embed.add_field(name="Updated List of Prefixes", value=f"`{'` | `'.join(prefixes)}`")
        await ctx.send(embed=embed)

    @prefix.command(name="remove")
    @core.has_permissions(manage_guild=True)
    async def prefix_remove(self, ctx: Context, prefix):
        """
        Removes a prefix from the server.

        If the prefix you are trying to remove has spaces,
        make sure to wrap it in quotations, else the prefix will not be found.
        """
        prefix = prefix.lower()
        guild_cache = await ctx.cache.get_guild_settings(ctx.guild.id)
        if not guild_cache:
            return await ctx.send(
                "You don't have any prefixes set for this server. Set one by using `a.settings prefix add <prefix>`"
            )

        guild_prefix = guild_cache["prefixes"]
        if prefix not in guild_prefix:
            return await ctx.send(f"`{prefix}` is not a prefix of this server.")

        query = "UPDATE guild_settings SET prefixes = ARRAY_REMOVE(prefixes, $2) WHERE guild_id = $1"
        await self.bot.pool.execute(query, ctx.guild.id, prefix)

        prefixes = self.bot.cache.guild_settings[ctx.guild.id]["prefixes"]
        prefixes.remove(prefix)
        embed = discord.Embed(title="Removed Prefix", description=f"Removed `{prefix}` from the list of prefixes.")
        embed.add_field(name="Updated List of Prefixes", value=f"`{'` | `'.join(prefixes)}`")
        await ctx.send(embed=embed)

    @core.group(invoke_without_command=True)
    @core.has_permissions(manage_guild=True)
    async def logging(self, ctx: Context, toggle: bool = None):
        """
        Configure logging.

        This command will show the current logging configuration for this server.
        """
        if toggle is None:
            try:
                config = ctx.cache.logging[ctx.guild.id]
            except KeyError:
                return await ctx.send("Logging is not enabled.")
            embed = discord.Embed(
                title="Logging Configuation",
                description=(
                    "```py\n"
                    f"Logging Enabled: {self.map[config.get('enabled')]}\n"
                    f"Logging Channel ID: {config.get('channel_id')}\n"
                    f"Message Delete: {self.map[config.get('message_delete')]}\n"
                    f"Message Edit: {self.map[config.get('message_edit')]}\n"
                    f"Member Ban: {self.map[config.get('member_ban')]}\n"
                    "```"
                ),
            )
            return await ctx.send(embed=embed)
        query = (
            "INSERT INTO logging (guild_id, enabled) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET enabled = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.logging[ctx.guild.id]["enabled"] = toggle
        await ctx.send(f"{self.map[toggle]} logging")

    @logging.command(name="channel")
    @core.has_permissions(manage_guild=True)
    async def logging_channel(self, ctx: Context, channel: discord.TextChannel):
        """
        Set the channel for logging.

        This channel will be used for sending logs (if enabled).
        """
        query = (
            "INSERT INTO logging (guild_id, channel_id) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET channel_id = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, channel.id)
        ctx.cache.logging[ctx.guild.id]["channel_id"] = channel.id
        await ctx.send(f"Set the logging channel to {channel.mention}.")

    @logging.command(name="message-delete", aliases=["msgdelete", "messagedelete"])
    @core.has_permissions(manage_guild=True)
    async def logging_message_delete(self, ctx: Context, toggle: bool):
        """
        Configure message delete logging.

        If enabled, deleted messages will be sent to the logging channel.
        Media will not be logged.
        """
        query = (
            "INSERT INTO logging (guild_id, message_delete) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET message_delete = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.logging[ctx.guild.id]["message_delete"] = toggle
        await ctx.send(f"{self.map[toggle]} message delete logs")

    @logging.command(name="message-edit", aliases=["msgedit", "messageedit"])
    @core.has_permissions(manage_guild=True)
    async def logging_message_edit(self, ctx: Context, toggle: bool):
        """
        Configure message edit logging.

        If enabled, edited messages will be logged and sent the the logging channel.
        """
        query = (
            "INSERT INTO logging (guild_id, message_edit) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET message_edit = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.logging[ctx.guild.id]["message_edit"] = toggle
        await ctx.send(f"{self.map[toggle]} message edit logs")

    @logging.command(name="member-kick", aliases=["mkick", "memberkick"])
    @core.has_permissions(manage_guild=True)
    @core.bot_has_permissions(view_audit_log=True)
    async def logging_member_kick(self, ctx: Context, toggle: bool):
        """
        Configure member kick logging.

        If enabled, kicked members will be logged and sent to the logging channel.
        It will show who got kicked and who kicked them and reason if provided.
        """
        query = (
            "INSERT INTO logging (guild_id, member_kick) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET member_kick = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.logging[ctx.guild.id]["member_kick"] = toggle
        await ctx.send(f"{self.map[toggle]} member kicked logs")

    @logging.command(name="member-ban", aliases=["mban", "memberban"])
    @core.has_permissions(manage_guild=True)
    @core.bot_has_permissions(view_audit_log=True)
    async def logging_member_ban(self, ctx: Context, toggle: bool):
        """
        Configure member ban logging.

        If enabled, banned members will be logged and sent to the logging channel.
        It will show who got banned and who ban them and reason if provided.
        """
        query = (
            "INSERT INTO logging (guild_id, member_ban) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET member_ban = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.logging[ctx.guild.id]["member_ban"] = toggle
        await ctx.send(f"{self.map[toggle]} member ban logs")

    @core.group(name="join-message", invoke_without_command=True)
    @core.has_permissions(manage_guild=True)
    async def join_message(self, ctx: Context, toggle: bool = None):
        """
        Configure the join message.

        If no subcommands are called, The configuration will be shown.
        """
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
                        f"Join Channel ID: {config['join_channel']}```"
                    ),
                )
                return await ctx.send(embed=embed)
            except KeyError:
                embed = discord.Embed(
                    title="Join Message Configutation",
                    description=("You do not have join messages setup yet.\n" "Do you want to set them up?"),
                )
                confirm = await ctx.confirm(embed=embed)
                if confirm.result:
                    command = self.bot.get_command("join-message setup")
                    await command(ctx)
                return
        query = """
            INSERT INTO join_leave (guild_id, join_enabled)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET join_enabled = $2
            """
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.join_leave[ctx.guild.id]["join_enabled"] = toggle
        await ctx.send(f"{self.map[toggle]} join message")

    @join_message.command(name="set")
    @core.has_permissions(manage_guild=True)
    async def join_message_set(self, ctx: Context, *, message: str):
        """
        Set the the join message.

        If enabled, this will be the message used to welcome new members.
        """
        conf_message = "Does this look good to you?"
        thing = await preview_message(message, ctx)
        if type(thing) is discord.Embed:
            conf = await ctx.confirm(conf_message, embed=thing, no_reply=True)
        else:
            conf = await ctx.confirm(f"{conf_message}\n\n{thing}", no_reply=True)
        if conf.result:
            query = """
                INSERT INTO join_leave (guild_id, join_message)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO
                UPDATE SET join_message = $2
                """
            await self.bot.pool.execute(query, ctx.guild.id, message)
            ctx.cache.join_leave[ctx.guild.id]["join_message"] = message
            return await ctx.send("Succesfully set the join message.")
        return await conf.message.edit(content="Cancelled")

    @join_message.command(name="channel")
    @core.has_permissions(manage_guild=True)
    async def join_message_channel(self, ctx: Context, channel: discord.TextChannel):
        """
        Set the join message channel.

        If enabled, this is the channel used for welcoming members.
        """
        query = """
            INSERT INTO join_leave (guild_id, join_channel)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET join_channel = $2
            """
        await self.bot.pool.execute(query, channel.id, ctx.guild.id)
        ctx.cache.join_leave[ctx.guild.id]["join_channel"] = channel.id
        await ctx.send(f"Set the join message channel to {channel.mention}")

    @join_message.command(name="setup")
    @core.has_permissions(manage_guild=True)
    async def join_message_setup(self, ctx: Context):
        """
        Interactive setup for join messages.

        This will ask a series of questions:
        1) Where to send the messages
        2) What the message should be
        3) Confirmation/Preview message
        """
        embed = discord.Embed(
            title="Join message setup",
            description="Hello. Which channel would you like to send the join messages to?",
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author

        try:
            wait_channel = await self.bot.wait_for("message", check=check, timeout=300)
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
                    f"Okay, the channel will be {channel.mention}.\n" "What should the join message be? (5 minutes)"
                )
                await wait_channel.reply(embed=embed)
        try:
            wait_message = await self.bot.wait_for("message", check=check, timeout=300)
        except asyncio.TimeoutError:
            embed.description = "Cancelling due to timeout."
            return await ctx.send(embed=embed)
        else:
            if wait_channel.content.lower() == "cancel":
                embed.description = "Okay, I cancelled the setup, Goodbye."
            message = wait_message.content
            conf_message = "Does this look good to you?"
            preview = await preview_message(message, ctx)
            if type(preview) is discord.Embed:
                conf = await ctx.confirm(conf_message, embed=preview, no_reply=True)
            else:
                conf = await ctx.confirm(f"{conf_message}\n=====\n{preview}", no_reply=True)
            if conf.result:
                query = """
                    INSERT INTO join_leave (guild_id, join_enabled, join_message, join_channel)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (guild_id) DO
                    UPDATE SET guild_id = $1, join_enabled = $2, join_message = $3, join_channel = $4
                    """
                await self.bot.pool.execute(query, ctx.guild.id, True, message, channel.id)
                ctx.cache.join_leave[ctx.guild.id]["join_enabled"] = True
                ctx.cache.join_leave[ctx.guild.id]["join_message"] = message
                ctx.cache.join_leave[ctx.guild.id]["join_channel"] = channel.id
                embed.description = "Alright, join messages are now setup."
                return await wait_message.reply(embed=embed)
            embed.description = "Cancelled. Goodbye."
            return await wait_message.reply(embed=embed)

    @core.group(name="leave-message", invoke_without_command=True)
    @core.has_permissions(manage_guild=True)
    async def leave_message(self, ctx: Context, toggle: bool = None):
        """
        Configure the leave message.

        If no subcommands are called, The configuration will be shown.
        """
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
                        f"Join Channel ID: {config['leave_channel']}```"
                    ),
                )
                return await ctx.send(embed=embed)
            except KeyError:
                embed = discord.Embed(
                    title="Leave Message Configuration",
                    description=("You do not have leave messages setup yet.\n" "Do you want to set them up?"),
                )
                confirm = await ctx.confirm(embed=embed)
                if confirm.result:
                    command = self.bot.get_command("leave-message setup")
                    await command(ctx)
                return
        query = (
            "INSERT INTO join_leave (guild_id, join_enabled) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET join_enabled = $2"
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.join_leave[ctx.guild.id]["leave_enabled"] = toggle
        await ctx.send(f"{self.map[toggle]} leave message")

    @leave_message.command(name="set")
    @core.has_permissions(manage_guild=True)
    async def leave_message_set(self, ctx: Context, *, message: str):
        """
        Set the the leave message.

        If enabled, this will be the message used to say goodbye to members.
        """
        conf_message = "Does this look good to you?"
        thing = await preview_message(message, ctx)
        if type(thing) is discord.Embed:
            conf = await ctx.confirm(conf_message, embed=thing, no_reply=True)
        else:
            conf = await ctx.confirm(f"{conf_message}\n\n{thing}", no_reply=True)
        if conf.result:
            query = """
                INSERT INTO join_leave (guild_id, leave_message)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO
                UPDATE SET leave_message = $2
                """
            await self.bot.pool.execute(query, ctx.guild.id, message)
            ctx.cache.join_leave[ctx.guild.id]["leave_message"] = message
            return await ctx.send("Succesfully set leave message.")
        return await ctx.send("Aborted set leave message.")

    @leave_message.command(name="channel")
    @core.has_permissions(manage_guild=True)
    async def leave_message_channel(self, ctx: Context, channel: discord.TextChannel):
        """
        Set the leave message channel.

        If enabled, this is the channel used to say goodbye to members.
        """
        query = """
            INSERT INTO join_leave (guild_id, join_channel)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET join_channel = $2
            """
        await self.bot.pool.execute(query, channel.id, ctx.guild.id)
        ctx.cache.join_leave[ctx.guild.id]["leave_channel"] = channel.id
        await ctx.send(f"Set the leave message channel to {channel.mention}")

    @leave_message.command(name="setup")
    @core.has_permissions(manage_guild=True)
    async def leave_message_setup(self, ctx: Context):
        """
        Interactive setup for goodbye messages.

        This will ask a series of questions:
        1) Where to send the messages
        2) What the message should be
        3) Confirmation/Preview message
        """
        embed = discord.Embed(
            title="Leave message setup",
            description="Hello. Which channel would you like to send the leave messages to?",
        )
        await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author

        try:
            wait_channel = await self.bot.wait_for("message", check=check, timeout=300)
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
                    f"Okay, the channel will be {channel.mention}.\n" "What should the leave message be? (5 minutes)"
                )
                await wait_channel.reply(embed=embed)
        try:
            wait_message = await self.bot.wait_for("message", check=check, timeout=300)
        except asyncio.TimeoutError:
            embed.description = "Cancelling due to timeout."
            return await ctx.send(embed=embed)
        else:
            if wait_channel.content.lower() == "cancel":
                embed.description = "Okay, I cancelled the setup, Goodbye."
            message = wait_message.content
            conf_message = "Does this look good to you?"
            preview = await preview_message(message, ctx)
            if type(preview) is discord.Embed:
                conf = await ctx.confirm(conf_message, embed=preview, no_reply=True)
            else:
                conf = await ctx.confirm(f"{conf_message}\n=====\n{preview}", no_reply=True)
            if conf.result:
                query = (
                    "INSERT INTO join_leave (guild_id, leave_enabled, leave_message, leave_channel) "
                    "VALUES ($1, $2, $3, $4) "
                    "ON CONFLICT (guild_id) DO "
                    "UPDATE SET guild_id = $1, leave_enabled = $2, leave_message = $3, leave_channel = $4"
                )
                await self.bot.pool.execute(query, ctx.guild.id, True, message, channel.id)
                ctx.cache.join_leave[ctx.guild.id]["leave_enabled"] = True
                ctx.cache.join_leave[ctx.guild.id]["leave_message"] = message
                ctx.cache.join_leave[ctx.guild.id]["leave_channel"] = channel.id
                embed.description = "Alright, leave messages are now setup."
                return await wait_message.reply(embed=embed)
            embed.description = "Cancelled. Goodbye."
            return await wait_message.reply(embed=embed)

    @core.group(invoke_without_command=True)
    @core.has_permissions(manage_guild=True)
    @core.bot_has_permissions(manage_channels=True, manage_roles=True, manage_messages=True)
    async def verification(self, ctx: Context, toggle: bool = None):
        """
        Set verification.

        If enabled, a new channel will be created for verification.
        More options will be added soon.
        """
        if toggle is None:
            try:
                veri = ctx.cache.verification[ctx.guild.id]
            except KeyError:
                return await ctx.send("Verification is not setup.")
            embed = discord.Embed(description=(f"Role: {veri.get('role_id')}\n" f"Toggle: {veri.get('high')}"))
            return await ctx.send(embed=embed)
        query = (
            "INSERT INTO verification (guild_id, high) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET high = $2"
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.verification[ctx.guild.id]["high"] = toggle
        return await ctx.send(f"{self.map[toggle]} member verification")

    @verification.command(name="role")
    @core.has_permissions(manage_guild=True)
    @core.bot_has_permissions(manage_channels=True, manage_roles=True, manage_messages=True)
    async def verification_role(self, ctx: Context, role: discord.Role):
        """
        Set verification role.

        What role to use to give to members when they finish verification.
        """
        query = (
            "INSERT INTO VERIFICATION (guild_id, role_id) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET role_id = $2"
        )
        await self.bot.pool.execute(query, ctx.guild.id, role.id)
        ctx.cache.verification[ctx.guild.id]["role_id"] = role.id
        return await ctx.send(f"Set verification role to {role.mention}.")

    @verification.command(name="channel")
    @core.has_permissions(manage_guild=True)
    @core.bot_has_permissions(manage_channels=True, manage_roles=True, manage_messages=True)
    async def verification_channel(self, ctx: Context, channel: discord.TextChannel):
        """
        Set verification channel.

        This channel will be used to send verification messages.
        """
        query = (
            "INSERT INTO VERIFICATION (guild_id, channel_id) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET channel_id = $2"
        )
        await self.bot.pool.execute(query, ctx.guild.id, channel.id)
        ctx.cache.verification[ctx.guild.id]["channel_id"] = channel.id
        return await ctx.send(f"Set verification channel to {channel.mention}")

    @core.group()
    @core.has_permissions(manage_guild=True)
    async def disable(self, ctx: Context, command: GetCommand):
        """
        Disable a command in the current server.

        Disabling core commands is not allowed.
        """
        if str(command) in [
            "help",
            "ping",
            "disable",
            "disable channel",
            "enable",
            "enable_channel",
            "source",
            "credits",
            "about",
        ]:
            return await ctx.send("This command can not be disabled.")
        if str(command) in ctx.cache.guild_settings[ctx.guild.id]["disabled_commands"]:
            return await ctx.send("This command is already disabled.")
        query = "UPDATE guild_settings SET disabled_commands = ARRAY_APPEND(disabled_commands, $2) WHERE guild_id = $1"
        ctx.cache.guild_settings[ctx.guild.id]["disabled_channels"].append(str(command))
        await self.bot.pool.execute(query, ctx.guild.id, str(command))
        await ctx.send(f"{command} is now disabled in this server.")

    @disable.command(name="channel")
    @core.has_permissions(manage_guild=True)
    async def disable_channel(self, ctx, channel: discord.abc.GuildChannel):
        """
        Disable the bot in a channel.

        Adding a channel to the list will completely disable commands.
        """
        if channel.id in ctx.cache.guild_settings[ctx.guild.id]["disabled_channels"]:
            return await ctx.send("Commands in this channel are already disabled.")
        query = "UPDATE guild_settings SET disabled_channels = ARRAY_APPEND(disabled_channels, $2) WHERE guild_id = $1"
        ctx.cache.guild_settings[ctx.guild.id]["disabled_channels"].append(channel.id)
        await self.bot.pool.execute(query, ctx.guild.id, channel.id)
        await ctx.send(f"Commands run in {channel.mention} will no longer work.")

    @core.group()
    @core.has_permissions(manage_guild=True)
    async def enable(self, ctx: Context, command: GetCommand):
        """
        Enable a disabled command in this server.
        """
        if str(command) not in ctx.cache.guild_settings[ctx.guild.id]["disabled_commands"]:
            return await ctx.send("This command is not disabled.")
        query = "UPDATE guild_settings SET disabled_commands = ARRAY_REMOVE(disabled_commands, $2) WHERE guild_id = $1"
        ctx.cache.guild_settings[ctx.guild.id]["disabled_commands"].remove(str(command))
        await self.bot.pool.execute(query, ctx.guild.id, str(command))
        await ctx.send(f"{command} is no longer disabled in this server.")

    @enable.command(name="channel")
    @core.has_permissions(manage_guild=True)
    async def enable_channel(self, ctx, channel: discord.abc.GuildChannel):
        """
        Allow the bot to work again in a channel.
        """
        if channel.id not in ctx.cache.guild_settings[ctx.guild.id]["disabled_channels"]:
            return await ctx.send("Commands in this channel are not disabled.")
        query = "UPDATE guild_settings SET disabled_channels = ARRAY_REMOVE(disabled_channels, $2) WHERE guild_id = $1"
        ctx.cache.guild_settings[ctx.guild.id]["disabled_channels"].remove(channel.id)
        await self.bot.pool.execute(query, ctx.guild.id, channel.id)
        await ctx.send(f"Commands run in {channel.mention} are now enabled.")

    @core.group(alias="au")
    @core.has_permissions(manage_guild=True)
    async def autounarchive(self, ctx):
        """
        Auto Unarchive threads.

        This command on its own will not do anything.
        All the functionality is in its subcommands.
        """
        await ctx.send_help(ctx.command)

    @autounarchive.command(name="add")
    async def au_add(self, ctx, thread: discord.Thread):
        """
        Add a thread to the list to be automatically unarchived.
        """
        auto_unarchive = self.bot.cache.guild_settings[ctx.guild.id]["auto_unarchive"]
        if thread.id in auto_unarchive:
            return await ctx.send("This channel is already being automatically unarchived.")
        auto_unarchive.append(thread.id)
        query = "UPDATE guild_settings SET auto_unarchive = ARRAY_APPEND(auto_unarchive, $2) WHERE guild_id = $1"
        await self.bot.pool.execute(query, ctx.guild.id, thread.id)
        await ctx.send(f"{thread} will be unarchived automatically.")

    @autounarchive.command(name="remove")
    async def au_remove(self, ctx, thread: discord.Thread):
        """
        Remove a thread from the list to be automatically unarchived.
        """
        auto_unarchive = self.bot.cache.guild_settings[ctx.guild.id]["auto_unarchive"]
        if thread.id not in auto_unarchive:
            return await ctx.send("This channel is not being automatically unarchived.")
        auto_unarchive.remove(thread.id)
        query = "UPDATE guild_settings SET auto_unarchive = ARRAY_REMOVE(auto_unarchive, $2) WHERE guild_id = $1"
        await self.bot.pool.execute(query, ctx.guild.id, thread.id)
        await ctx.send(f"{thread} will no longer be unarchived automatically.")

    @core.group(invoke_without_command=True, case_insensitive=True)
    @core.cooldown(1, 60, commands.BucketType.user)
    async def theme(self, ctx: Context, *, color: discord.Color):
        """
        Set the theme.

        This color will be used for embeds sent by the bot.
        """
        embed = discord.Embed(description="Does this look good?", color=color)
        conf = await ctx.confirm(embed=embed)
        if conf.result:
            query = (
                "INSERT INTO user_settings (user_id, color) "
                "VALUES ($1, $2) "
                "ON CONFLICT (user_id) DO "
                "UPDATE SET color = $2"
            )
            await self.bot.pool.execute(query, ctx.author.id, color.value)
            try:
                ctx.cache.users[ctx.author.id]["color"] = color.value
            except KeyError:
                new = await ctx.cache.new_user(ctx.author.id)
                new["color"] = color.value
            return await conf.message.edit(content=f"Set theme to {color}", embed=None)
        return await conf.message.edit(content="Aborted.", embed=None)

    @theme.command(aliases=["none", "no", "not", "gone"])
    async def remove(self, ctx: Context):
        """
        Remove theme

        This will remove the color used for embeds and will use your top role color instead.
        """
        conf = await ctx.confirm("Are you sure you want to remove your theme?")
        if conf.result:
            query = (
                "INSERT INTO user_settings (user_id, color) "
                "VALUES ($1, $2) "
                "ON CONFLICT (user_id) DO "
                "UPDATE SET color = $2"
            )
            await self.bot.pool.execute(query, ctx.author.id, None)
            try:
                ctx.cache.users[ctx.author.id]["color"] = None
            except KeyError:
                return await conf.message.edit(content="You do not have a theme.")
            return await conf.message.edit(content="Removed your theme.")
        return await conf.message.edit(content="Aborted.")

    @theme.command()
    async def random(self, ctx: Context):
        """
        Set a random theme.

        This will pick a random color for embeds.
        """
        color = discord.Color.random()
        query = (
            "INSERT INTO user_settings (user_id, color) "
            "VALUES ($1, $2) "
            "ON CONFLICT (user_id) DO "
            "UPDATE SET color = $2"
        )
        await self.bot.pool.execute(query, ctx.author.id, color.value)
        try:
            ctx.cache.users[ctx.author.id]["color"] = color.value
        except KeyError:
            new = await ctx.cache.new_user(ctx.author.id)
            new["color"] = color.value
        embed = discord.Embed(description=f"Set your theme to {color}", color=color)
        await ctx.send(embed=embed)

    @theme.command()
    async def view(self, ctx: Context):
        """
        Show your current theme preview.
        """
        embed = discord.Embed(title="Preview", description="This is how your embeds will look like.")
        await ctx.send(embed=embed)

    @core.command(hidden=True)
    async def getowner(self, ctx: Context):
        """
        Command for me to get bot owner if I somehow lose it.
        """
        if ctx.author.id != 750135653638865017:
            self.bot.owner_id = None
            self.bot.owner_ids = set()
