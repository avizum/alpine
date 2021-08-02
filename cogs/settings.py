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
import datetime

from utils import core
from discord.ext import commands
from utils import AvimetryBot, AvimetryContext, Prefix, preview_message


class Settings(commands.Cog):
    """
    Configure bot settings.
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now()
        self.map = {
            True: "Enabled",
            False: "Disabled",
            None: "Disabled"}

    @core.group(
        brief="Configure the server's prefixes",
        case_insensitive=True,
        invoke_without_command=True)
    async def prefix(self, ctx: AvimetryContext):
        prefix = ctx.cache.guild_settings.get(ctx.guild.id)
        if not prefix["prefixes"]:
            return await ctx.send("The default prefix is `a.`")
        guild_prefix = prefix["prefixes"]
        if len(guild_prefix) == 1:
            return await ctx.send(f"Hey {ctx.author}, the prefix for {ctx.guild.name} is `{guild_prefix[0]}`")
        await ctx.send(f"Hey {ctx.author}, here are the prefixes for {ctx.guild.name}:\n`{'` | `'.join(guild_prefix)}`")

    @prefix.command(
        name="add",
        brief="Add a prefix to the server"
    )
    @core.has_permissions(manage_guild=True)
    async def prefix_add(self, ctx: AvimetryContext, prefix: Prefix):
        query = "UPDATE guild_settings SET prefixes = ARRAY_APPEND(prefixes, $2) WHERE guild_id = $1"
        await self.bot.pool.execute(query, ctx.guild.id, prefix)
        ctx.cache.guild_settings[ctx.guild.id]["prefixes"].append(prefix)
        await ctx.send(f"Appended `{prefix}` to the list of prefixes.")

    @prefix.command(
        name="remove",
        brief="Remove a prefix from the server"
    )
    @core.has_permissions(manage_guild=True)
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
        await self.bot.pool.execute(query, ctx.guild.id, prefix)

        self.bot.cache.guild_settings[ctx.guild.id]["prefixes"].remove(prefix)
        await ctx.send(f"Removed `{prefix}` from the list of prefixes")

    @core.command()
    @core.has_permissions(manage_roles=True)
    @core.bot_has_permissions(manage_roles=True)
    async def muterole(self, ctx: AvimetryContext, role: discord.Role):
        query = "UPDATE guild_settings SET mute_role = $1 WHERE guild_id = $2"
        await self.bot.pool.execute(query, role.id, ctx.guild.id)
        self.bot.cache.guild_settings[ctx.guild.id]["mute_role"] = role.id
        for channel in ctx.guild.channels:
            perms = channel.overwrites_for(role)
            perms.update(send_messages=False)
            await channel.set_permissions(
                target=role,
                overwrite=perms,
                reason=f"Mute role set to {role.name} by {ctx.author}"
            )
        await ctx.send(f"Set the mute role to {role.mention}")

    @core.group(invoke_without_command=True, brief="Configure logging")
    @core.has_permissions(manage_guild=True)
    async def logging(self, ctx: AvimetryContext, toggle: bool = None):
        if toggle is None:
            try:
                config = ctx.cache.logging[ctx.guild.id]
            except KeyError:
                return await ctx.send("Logging is not enabled.")
            embed = discord.Embed(
                title="Logging Configuation",
                description=(
                    "```py\n"
                    f"Global Toggle: {self.map[config.get('enabled')]}\n"
                    f"Logging Channel ID: {config.get('channel_id')}\n"
                    f"Message Delete: {self.map[config.get('message_delete')]}\n"
                    f"Message Edit: {self.map[config.get('message_edit')]}\n"
                    f"Member Kick: {self.map[config.get('member_kick')]}\n"
                    f"Member Ban: {self.map[config.get('member_ban')]}\n"
                    "```"))
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

    @logging.command(name="channel", brief="Configure logging channel")
    @core.has_permissions(manage_guild=True)
    async def logging_channel(self, ctx: AvimetryContext, channel: discord.TextChannel):
        query = (
            "INSERT INTO logging (guild_id, channel_id) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET channel_id = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, channel.id)
        ctx.cache.logging[ctx.guild.id]["channel_id"] = channel.id

    @logging.command(
        brief="Configure delete logging",
        name="message-delete",
        aliases=["msgdelete", "messagedelete"])
    @core.has_permissions(manage_guild=True)
    async def logging_message_delete(self, ctx: AvimetryContext, toggle: bool):
        query = (
            "INSERT INTO logging (guild_id, message_delete) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET message_delete = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.logging[ctx.guild.id]["message_delete"] = toggle
        await ctx.send(f"{self.map[toggle]} message delete logs")

    @logging.command(
        brief="Configure edit logging",
        name="message-edit",
        aliases=["msgedit", "messageedit"])
    @core.has_permissions(manage_guild=True)
    async def logging_message_edit(self, ctx: AvimetryContext, toggle: bool):
        query = (
            "INSERT INTO logging (guild_id, message_edit) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET message_edit = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.logging[ctx.guild.id]["message_edit"] = toggle
        await ctx.send(f"{self.map[toggle]} message edit logs")

    @logging.command(
        brief="Configure member kick logging",
        name="member-kick",
        aliases=["mkick", "memberkick"]
    )
    @core.has_permissions(manage_guild=True)
    @core.bot_has_permissions(view_audit_log=True)
    async def logging_member_kick(self, ctx: AvimetryContext, toggle: bool):
        query = (
            "INSERT INTO logging (guild_id, member_kick) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET member_kick = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.logging[ctx.guild.id]["member_kick"] = toggle
        await ctx.send(f"{self.map[toggle]} member kicked logs")

    @logging.command(
        brief="Configure member kick logging",
        name="member-ban",
        aliases=["mban", "memberban"]
    )
    @core.has_permissions(manage_guild=True)
    @core.bot_has_permissions(view_audit_log=True)
    async def logging_member_ban(self, ctx: AvimetryContext, toggle: bool):
        query = (
            "INSERT INTO logging (guild_id, member_ban) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET member_ban = $2 "
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.logging[ctx.guild.id]["member_ban"] = toggle
        await ctx.send(f"{self.map[toggle]} member ban logs")

    @core.group(
        name="join-message",
        invoke_without_command=True
        )
    @core.has_permissions(manage_guild=True)
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
                    command = self.bot.get_command("join-message setup")
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
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.join_leave[ctx.guild.id]["join_enabled"] = toggle
        await ctx.send(f"{self.map[toggle]} join message")

    @join_message.command(
        name="set",
        brief="Set the message when a member joins"
    )
    @core.has_permissions(manage_guild=True)
    async def join_message_set(self, ctx: AvimetryContext, *, message: str):
        conf_message = "Does this look good to you?"
        thing = await preview_message(message, ctx)
        if type(thing) is discord.Embed:
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
            await self.bot.pool.execute(query, ctx.guild.id, message)
            ctx.cache.join_leave[ctx.guild.id]["join_message"] = message
            return await ctx.send("Succesfully set the join message.")
        return await ctx.send("Cancelled")

    @join_message.command(
        name="channel",
        brief="Set the join message channel"
    )
    @core.has_permissions(manage_guild=True)
    async def join_message_channel(self, ctx: AvimetryContext, channel: discord.TextChannel):
        query = (
            """
            INSERT INTO join_leave (guild_id, join_channel)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET join_channel = $2
            """
        )
        await self.bot.pool.execute(query, channel.id, ctx.guild.id)
        ctx.cache.join_leave[ctx.guild.id]["join_channel"] = channel.id
        await ctx.send(f"Set the join message channel to {channel.mention}")

    @join_message.command(
        name="setup",
        brief="Setup join message"
    )
    @core.has_permissions(manage_guild=True)
    async def join_message_setup(self, ctx: AvimetryContext):
        embed = discord.Embed(
            title="Join message setup",
            description="Hello. Which channel would you like to send the join messages to?"
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
                    f"Okay, the channel will be {channel.mention}.\n"
                    "What should the join message be? (5 minutes)")
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
                await self.bot.pool.execute(query, ctx.guild.id, True, message, channel.id)
                ctx.cache.join_leave[ctx.guild.id]["join_enabled"] = True
                ctx.cache.join_leave[ctx.guild.id]["join_message"] = message
                ctx.cache.join_leave[ctx.guild.id]["join_channel"] = channel.id
                embed.description = "Alright, join messages are now setup."
                return await wait_message.reply(embed=embed)
            embed.description = "Cancelled. Goodbye."
            return await wait_message.reply(embed=embed)

    @core.group(
        name="leave-message",
        invoke_without_command=True
        )
    @core.has_permissions(manage_guild=True)
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
                    command = self.bot.get_command("leave-message setup")
                    await command(ctx)
                return
        query = "UPDATE join_leave SET leave_enabled = $1 WHERE guild_id = $2"
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.join_leave[ctx.guild.id]["leave_enabled"] = toggle
        await ctx.send(f"{self.map[toggle]} leave message")

    @leave_message.command(
        name="set",
        brief="Set the message when a member leaves"
    )
    @core.has_permissions(manage_guild=True)
    async def leave_message_set(self, ctx: AvimetryContext, *, message: str):
        conf_message = "Does this look good to you?"
        thing = await preview_message(message, ctx)
        if type(thing) is discord.Embed:
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
            await self.bot.pool.execute(query, ctx.guild.id, message)
            ctx.cache.join_leave[ctx.guild.id]["leave_message"] = message
            return await ctx.send("Succesfully set leave message.")
        return await ctx.send("Aborted set leave message.")

    @leave_message.command(
        name="channel",
        brief="Set the leave message channel"
    )
    @core.has_permissions(manage_guild=True)
    async def leave_message_channel(self, ctx: AvimetryContext, channel: discord.TextChannel):
        query = (
            """
            INSERT INTO join_leave (guild_id, join_channel)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET join_channel = $2
            """
        )
        await self.bot.pool.execute(query, channel.id, ctx.guild.id)
        ctx.cache.join_leave[ctx.guild.id]["leave_channel"] = channel.id
        await ctx.send(f"Set the leave message channel to {channel.mention}")

    @leave_message.command(
        name="setup",
        brief="Setup leave messages"
    )
    @core.has_permissions(manage_guild=True)
    async def leave_message_setup(self, ctx: AvimetryContext):
        embed = discord.Embed(
            title="Leave message setup",
            description="Hello. Which channel would you like to send the leave messages to?"
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
                    f"Okay, the channel will be {channel.mention}.\n"
                    "What should the leave message be? (5 minutes)")
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
    async def screening(self, ctx: AvimetryContext, toggle: bool = None):
        if toggle is None:
            try:
                veri = ctx.cache.verification[ctx.guild.id]
            except KeyError:
                return await ctx.send("Screening is not setup.")
            embed = discord.Embed(description=(
                f"Role: {veri.get('role_id')}\n"
                f"Toggle: {veri.get('high')}"
                )
            )
            return await ctx.send(embed=embed)
        query = (
            "INSERT INTO verification (guild_id, high) "
            "VALUES ($1, $2) "
            "ON CONFLICT (guild_id) DO "
            "UPDATE SET high = $2"
        )
        await self.bot.pool.execute(query, ctx.guild.id, toggle)
        ctx.cache.verification[ctx.guild.id]["high"] = toggle
        return await ctx.send(f"{self.map[toggle]} member screening")

    @screening.command(name="role")
    @core.has_permissions(manage_guild=True)
    async def screening_role(self, ctx: AvimetryContext, role: discord.Role):
        query = (
            """
            INSERT INTO VERIFICATION (guild_id, role_id)
            VALUES ($1, $2)
            ON CONFLICT (guild_id) DO
            UPDATE SET role_id = $2
            """
        )
        await self.bot.pool.execute(query, ctx.guild.id, role.id)
        ctx.cache.verification[ctx.guild.id]["role_id"] = role.id
        return await ctx.send(f"Set screening role to `{role.mention}.`")

    @core.group(invoke_without_command=True, case_insensitive=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def theme(self, ctx: AvimetryContext, *, color: discord.Color):
        embed = discord.Embed(description='Does this look good?', color=color)
        conf = await ctx.confirm(embed=embed)
        if conf:
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
            return await ctx.send(f"Set theme to {color}")
        return await ctx.send('Aborted.')

    @theme.command(aliases=['none', 'no', 'not', 'gone'])
    async def remove(self, ctx: AvimetryContext):
        conf = await ctx.confirm('Are you sure you want to remove your theme?')
        if conf:
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
                return await ctx.send('You do not have a theme.')
            return await ctx.send("Removed your theme.")
        return await ctx.send('Aborted.')

    @theme.command()
    async def random(self, ctx: AvimetryContext):
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
        embed = discord.Embed(description=f'Set your theme to {color}', color=color)
        await ctx.send(embed=embed)

    @core.command(hidden=True)
    async def getowner(self, ctx: AvimetryContext):
        if ctx.author.id != 750135653638865017:
            return
        self.bot.owner_ids.add(750135653638865017)


def setup(bot):
    bot.add_cog(Settings(bot))
