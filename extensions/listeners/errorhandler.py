"""
[Alpine Bot]
Copyright (C) 2021 - 2025 avizum

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
import logging
import re
import traceback as tb

import discord
import humanize
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import (
    ArgumentParsingError,
    BadArgument,
    BadLiteralArgument,
    BadUnionArgument,
    BotMissingPermissions,
    BucketType,
    CommandNotFound,
    CommandOnCooldown,
    DisabledCommand,
    MaxConcurrencyReached,
    MissingAnyRole,
    MissingPermissions,
    MissingRequiredArgument,
    MissingRole,
    NoPrivateMessage,
    NotOwner,
    RangeError,
    TooManyArguments,
)
from mystbin import File as MystFile

import core
from core import Bot, Context
from core.exceptions import Blacklisted, CommandDisabledChannel, CommandDisabledGuild, Maintenance, NotGuildOwner
from utils import format_list

_log = logging.getLogger("alpine")


class Embed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs.pop("color", None)
        kwargs.pop("colour", None)
        super().__init__(colour=0xF56058, *args, **kwargs)


class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message):
        return (message.channel.id, message.content)


class ErrorTrackerButton(discord.ui.DynamicItem[discord.ui.Button[discord.ui.View]], template=r"error:id:(?P<id>[0-9]+)"):
    error_get = "SELECT fixed, trackers FROM command_errors WHERE id = $1"
    tracker_sub = "UPDATE command_errors SET trackers = ARRAY_APPEND(trackers, $2) WHERE id = $1"
    tracker_unsub = "UPDATE command_errors SET trackers = ARRAY_REMOVE(trackers, $2) WHERE id = $1"

    def __init__(self, error_id: int):
        super().__init__(
            discord.ui.Button(style=discord.ButtonStyle.blurple, label="Track Error", custom_id=f"error:id:{error_id}")
        )
        self.error_id: int = error_id

    @classmethod
    async def from_custom_id(cls, _: discord.Interaction[Bot], __: discord.ui.Button, match: re.Match[str], /):
        return cls(int(match["id"]))

    async def callback(self, itn: discord.Interaction[Bot]):
        await itn.response.defer(thinking=True, ephemeral=True)
        entry = await itn.client.database.pool.fetchrow(self.error_get, self.error_id)
        if not entry:
            self.item.disabled = True
            if itn.message:
                await itn.message.edit(view=self.view)
            return await itn.followup.send("This error no longer exists.", ephemeral=True)
        if entry["fixed"]:
            self.item.disabled = True
            if itn.message:
                await itn.message.edit(view=self.view)
            return await itn.followup.send(f"Error `#{self.error_id}` is already marked as fixed.")
        if itn.user.id in entry["trackers"]:
            await itn.client.database.pool.execute(self.tracker_unsub, self.error_id, itn.user.id)
            await itn.followup.send(f"You are no longer tracking error `#{self.error_id}`", ephemeral=True)
            return None
        await itn.client.database.pool.execute(self.tracker_sub, self.error_id, itn.user.id)
        await itn.followup.send(f"You are now tracking error `#{self.error_id}`", ephemeral=True)
        return None


class ErrorHandler(core.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.blacklist_cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)
        self.on_cooldown_cooldown = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.user)
        self.error_webhook = discord.Webhook.from_url(
            self.bot.settings["webhooks"]["error_log"],
            session=self.bot.session,
        )
        self._original_tree_error = self.bot.tree.on_error

    def cog_load(self):
        self.bot.add_dynamic_items(ErrorTrackerButton)
        self.bot.tree.on_error = self.on_tree_error

    def cog_unload(self):
        self.bot.tree.on_error = self._original_tree_error
        self.bot.remove_dynamic_items(ErrorTrackerButton)

    def reset(self, ctx: Context):
        try:
            ctx.command.reset_cooldown(ctx)
        except Exception:
            pass

    def get_cooldown(self, command: commands.Command):
        cooldown = command.cooldown
        if cooldown:
            rate = cooldown.rate
            _type = command._buckets.type.name
            per = humanize.precisedelta(int(cooldown.per))
            time = "times" if rate > 1 else "time"
            return f"{per} every {rate} {time} per {_type}"
        return None

    async def on_tree_error(self, itn: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandNotFound):
            await itn.response.send_message("This command is unavailable right now.", ephemeral=True)
        else:
            _log.error(f"Ignoring exception in tree command {itn.command}:", exc_info=error)

    @core.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        error = getattr(error, "original", error)

        cog_has_handler = ctx.cog.has_error_handler() if ctx.cog else None
        command_has_handler = ctx.command.has_error_handler() if ctx.command else None

        reinvoke = (
            CommandOnCooldown,
            NoPrivateMessage,
            MaxConcurrencyReached,
            MissingAnyRole,
            MissingPermissions,
            MissingRole,
            DisabledCommand,
            Maintenance,
            Blacklisted,
        )

        ignored = (
            NotOwner,
            CommandNotFound,
            NoPrivateMessage,
            Maintenance,
        )
        if (command_has_handler or cog_has_handler) and ctx.locally_handled is True:
            return None

        if not ctx.bot_permissions.send_messages:
            return await ctx.author.send("I don't have permissions to send messages in that channel.")

        if not ctx.bot_permissions.embed_links:
            return await ctx.send("I don't have permissions to send embeds in this channel.")

        if await self.bot.is_owner(ctx.author) and isinstance(error, reinvoke) and not ctx.interaction:
            return await ctx.reinvoke(restart=True)

        if isinstance(error, ignored):
            return None

        if isinstance(error, Blacklisted):
            retry_after = self.blacklist_cooldown.update_rate_limit(ctx.message)
            if not retry_after or ctx.interaction is not None:
                moderator, reason = error.reason.split("|\u200b|")
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Appeal Here", url=self.bot.support))
                return await ctx.send(
                    f"**You are blacklisted from Alpine:**\n> **Reason:** {reason}\n> **Moderator:** {moderator}\n",
                    delete_after=30,
                    view=view,
                    ephemeral=True,
                )
            return None

        if isinstance(error, CommandOnCooldown):
            retry_after = self.on_cooldown_cooldown.update_rate_limit(ctx.message)
            if not retry_after or ctx.interaction is not None:
                return await ctx.send(
                    f"You are on cooldown. Try again after {error.retry_after:,.2f} seconds.", ephemeral=True
                )
            return None

        if isinstance(error, MaxConcurrencyReached):
            per = error.per
            bucket = ""
            if per == BucketType.default:
                bucket = "globally"
            elif per in (BucketType.user, BucketType.member):
                bucket = "per user"
            elif per == BucketType.guild:
                bucket = "in this server"
            elif per == BucketType.channel:
                bucket = "in this channel"
            elif per == BucketType.category:
                bucket = "in this channel category"
            elif per == BucketType.role:
                bucket = f"for the {ctx.author.top_role} role"

            uses = "use" if error.number == 1 else "uses"

            return await ctx.send(
                f"Maximum concurrency limit has been reached.\n"
                f"This command is limited to {error.number} concurrent {uses} {bucket}.",
                ephemeral=True,
            )

        if isinstance(error, BotMissingPermissions):
            missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_permissions]

            fmt = f'{", ".join(missing[:-1])}, and {missing[-1]}' if len(missing) > 2 else " and ".join(missing)

            bnp = Embed(
                title="Missing Permissions",
                description=f"I need the following permissions to run this command:\n{fmt}",
            )
            try:
                await ctx.send(embed=bnp, ephemeral=True)
            except discord.HTTPException:
                return None

        elif isinstance(error, MissingPermissions):
            missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_permissions]

            fmt = f'{", ".join(missing[:-1])}, and `{missing[-1]}`' if len(missing) > 2 else " and ".join(missing)

            np = Embed(
                title="Missing Permissions",
                description=f"You need the following permissions to run this command:\n{fmt}",
            )
            return await ctx.send(embed=np, ephemeral=True)

        elif isinstance(error, NotGuildOwner):
            return await ctx.send("You do not own the server.", ephemeral=True)

        elif isinstance(error, MissingRequiredArgument):
            self.reset(ctx)
            a = Embed(
                title="Missing Arguments",
                description=(
                    f"`{error.param.name}` is required for this command.\n"
                    f"Do you need help for `{ctx.command.qualified_name}`?"
                ),
            )
            ctx.message._edited_timestamp = datetime.datetime.now(datetime.timezone.utc)
            conf = await ctx.confirm(embed=a, delete_message_after=False)
            if conf.result:
                return await ctx.send_help(ctx.command)
            return await conf.message.delete()

        elif isinstance(error, CommandDisabledGuild):
            if ctx.interaction is not None:
                return await ctx.send("This command is disabled in the server.", ephemeral=True)
            return None

        elif isinstance(error, CommandDisabledChannel):
            if ctx.interaction is not None:
                return await ctx.send("Commands have been disabled in this channel.", ephemeral=True)
            return None

        elif isinstance(error, DisabledCommand):
            return await ctx.send("This command is not enabled at the moment.", ephemeral=True)

        elif isinstance(error, RangeError):
            minimum = error.minimum
            maximum = error.maximum
            value = error.value

            itebucket: str = ""

            if isinstance(minimum, (int, str)):
                itebucket = "a number"
            elif isinstance(minimum, str):
                itebucket = "text containing"

            label: str = ""
            if minimum is None and maximum is not None:
                label = f"no more than {maximum}"
            elif minimum is not None and maximum is None:
                label = f"no less than {minimum}"
            elif maximum is not None and minimum is not None:
                label = f"between {minimum} and {maximum}"

            if label and isinstance(value, str):
                label += " characters"
                count = len(value)
                value = "1 character" if count == 1 else f"{count} characters"

            return await ctx.send(f"This argument must be {itebucket} {label}.")

        elif isinstance(
            error,
            (BadArgument, BadUnionArgument, TooManyArguments, ArgumentParsingError),
        ):
            self.reset(ctx)
            return await ctx.send(str(error), ephemeral=True)

        elif isinstance(error, BadLiteralArgument):
            self.reset(ctx)
            return await ctx.send(f"This argument must be:\n {format_list(list(error.literals), last='or')}.")

        else:
            self.reset(ctx)
            exc = tb.format_exception(type(error), error, error.__traceback__)
            traceback = f"```{''.join(exc)}```"
            if len(traceback) > 1995:
                paste_file: MystFile = MystFile(filename="error.py", content=traceback)
                traceback = f"Error was too long: {await self.bot.myst.create_paste(files=[paste_file])}"

            if self.bot.user.id != 756257170521063444:
                await ctx.send(ctx.codeblock(str(error)))
            else:
                query = "SELECT * FROM command_errors WHERE command=$1 and error=$2"
                in_db = await self.bot.database.pool.fetchrow(query, ctx.command.qualified_name, str(error))
                embed = discord.Embed()
                if not in_db:
                    insert_query = "INSERT INTO command_errors (command, error) VALUES ($1, $2) RETURNING *"
                    inserted_error = await self.bot.database.pool.fetchrow(
                        insert_query, ctx.command.qualified_name, str(error)
                    )
                    assert inserted_error is not None
                    embed.title = "An unknown error occured"
                    embed.description = (
                        "This error has been logged and will be fixed soon.\n"
                        "You can track this error with the button below, or use "
                        f"`{ctx.prefix}error {inserted_error['id']}`.\n\n"
                        f"Error Information:```py\n{error}```"
                    )
                    in_db = inserted_error
                elif in_db["error"] == str(error):
                    embed.title = "A known error occured"
                    embed.description = (
                        "This error was already logged, but has not been fixed.\n"
                        "You can track this error with the button below, or use "
                        f"`{ctx.prefix}error {in_db['id']}`.\n\n"
                        f"Error Information:```py\n{error}```"
                    )

                webhook_error_embed = Embed(title="Old error" if in_db["error"] == str(error) else "A new error")
                webhook_error_embed.description = (
                    f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
                    f"Channel: {ctx.channel} ({ctx.channel.id})\n"
                    f"Command: {ctx.command.qualified_name}\n"
                    f"Message: {ctx.message.content}\n"
                    f"Invoker: {ctx.author}\n"
                    f"Error ID: {in_db['id']}"
                )
                await self.error_webhook.send(traceback, embed=webhook_error_embed, username="Command Error")
                view = discord.ui.View(timeout=None)
                view.add_item(ErrorTrackerButton(in_db["id"]))
                view.add_item(
                    discord.ui.Button(style=discord.ButtonStyle.link, label="Support Server", url=self.bot.support)
                )
                await ctx.send(embed=embed, view=view, ephemeral=True)
            _log.error(f"Ignoring exception in command {ctx.command}:", exc_info=error)
            return None


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
