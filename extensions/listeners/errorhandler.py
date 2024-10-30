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

import datetime
import logging
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
from utils import View, format_list

_log = logging.getLogger("alpine")


class Embed(discord.Embed):
    def __init__(self, *args, **kwargs):
        kwargs.pop("color", None)
        kwargs.pop("colour", None)
        super().__init__(colour=0xF56058, *args, **kwargs)


class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message):
        return (message.channel.id, message.content)


class UnknownError(View):
    def __init__(self, *, member: discord.Member, bot: Bot, error_id: int):
        self.error_id = error_id
        self.bot = bot
        super().__init__(member=member, timeout=3600)
        support = discord.ui.Button(style=discord.ButtonStyle.link, label="Support Server", url=self.bot.support)
        self.add_item(support)
        self.message: discord.Message | None = None
        self.cooldown = commands.CooldownMapping.from_cooldown(2, 60, commands.BucketType.user)

    async def interaction_check(self, interaction: discord.Interaction):
        return True

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    @discord.ui.button(label="Track Error", style=discord.ButtonStyle.blurple)
    async def track_error(self, interaction: discord.Interaction, button: discord.ui.Button):
        assert self.message is not None
        retry = self.cooldown.update_rate_limit(self.message)
        if retry:
            return await interaction.response.send_message(
                f"You are doing that too fast. Please try again in {retry:,.2f} seconds.",
                ephemeral=True,
            )
        check = await self.bot.database.pool.fetchrow("SELECT trackers FROM command_errors WHERE id = $1", self.error_id)
        if not check:
            return await interaction.response.send_message("Something broke.", ephemeral=True)
        if self.member.id in check["trackers"]:
            remove_tracker = "UPDATE command_errors SET trackers = ARRAY_REMOVE(trackers, $2) WHERE id = $1"
            await self.bot.database.pool.execute(remove_tracker, self.error_id, self.member.id)
            return await interaction.response.send_message(f"No longer tracking Error #{self.error_id}", ephemeral=True)
        add_tracker = "UPDATE command_errors SET trackers = ARRAY_APPEND(trackers, $2) WHERE id = $1"
        await self.bot.database.pool.execute(add_tracker, self.error_id, self.member.id)
        return await interaction.response.send_message(f"Now tracking Error #{self.error_id}.", ephemeral=True)


class ErrorHandler(core.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.blacklist_cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)
        self.on_cooldown_cooldown = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.user)
        self.max_concurrency_cooldown = commands.CooldownMapping.from_cooldown(1, 30, commands.BucketType.user)
        self.maintenance_cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.channel)
        self.no_dm_command_cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)
        self.not_found_cooldown_content = CooldownByContent.from_cooldown(1, 15, commands.BucketType.user)
        self.not_found_cooldown = commands.CooldownMapping.from_cooldown(2, 30, commands.BucketType.user)
        self.disabled_channel = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.channel)
        self.disabled_command = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.channel)
        self.error_webhook = discord.Webhook.from_url(
            self.bot.settings["webhooks"]["error_log"],
            session=self.bot.session,
        )
        self._original_tree_error = self.bot.tree.on_error
        self.bot.tree.on_error = self.on_tree_error

    async def cog_unload(self):
        self.bot.tree.on_error = self._original_tree_error

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
            return await itn.response.send_message("This command is unavailable right now.", ephemeral=True)
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
            return

        if not ctx.bot_permissions.send_messages:
            return await ctx.author.send("I don't have permissions to send messages in that channel.")

        if not ctx.bot_permissions.embed_links:
            return await ctx.send("I don't have permissions to send embeds in this channel.")

        if await self.bot.is_owner(ctx.author) and isinstance(error, reinvoke):
            try:
                return await ctx.reinvoke(restart=True)
            except Exception:
                pass
        elif await self.bot.is_owner(ctx.author) and ctx.prefix == "" and isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, ignored):
            return

        elif isinstance(error, Blacklisted):
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

        elif isinstance(error, CommandOnCooldown):
            retry_after = self.on_cooldown_cooldown.update_rate_limit(ctx.message)
            if not retry_after or ctx.interaction is not None:
                return await ctx.send(
                    f"You are on cooldown. Try again after {error.retry_after:,.2f} seconds.", ephemeral=True
                )

        elif isinstance(error, MaxConcurrencyReached):
            per = error.per
            bucket = ""
            if per == BucketType.default:
                bucket = "globally"
            elif per == BucketType.user or per == BucketType.member:
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

        elif isinstance(error, BotMissingPermissions):
            missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_permissions]

            if len(missing) > 2:
                fmt = f'{", ".join(missing[:-1])}, and {missing[-1]}'
            else:
                fmt = " and ".join(missing)

            bnp = Embed(
                title="Missing Permissions",
                description=f"I need the following permissions to run this command:\n{fmt}",
            )
            try:
                await ctx.send(embed=bnp, ephemeral=True)
            except discord.HTTPException:
                return

        elif isinstance(error, MissingPermissions):
            missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_permissions]

            if len(missing) > 2:
                fmt = f'{", ".join(missing[:-1])}, and `{missing[-1]}`'
            else:
                fmt = " and ".join(missing)

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
            retry_after = self.disabled_command.update_rate_limit(ctx.message)
            if not retry_after or ctx.interaction is not None:
                return await ctx.send("This command is disabled in the server.", ephemeral=True)

        elif isinstance(error, CommandDisabledChannel):
            retry_after = self.disabled_channel.update_rate_limit(ctx.message)
            if not retry_after or ctx.interaction is not None:
                return await ctx.send("Commands have been disabled in this channel.", ephemeral=True)

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
                if count == 1:
                    value = "1 character"
                else:
                    value = f"{count} characters"

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
            query = "SELECT * FROM command_errors WHERE command=$1 and error=$2"
            in_db = await self.bot.database.pool.fetchrow(query, ctx.command.qualified_name, str(error))
            embed = discord.Embed()
            if not in_db:
                insert_query = "INSERT INTO command_errors (command, error) " "VALUES ($1, $2) " "RETURNING *"
                inserted_error = await self.bot.database.pool.fetchrow(insert_query, ctx.command.qualified_name, str(error))
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

            webhook_error_embed = Embed(title="Old error" if in_db else "A new error")
            webhook_error_embed.description = (
                f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
                f"Channel: {ctx.channel} ({ctx.channel.id})\n"
                f"Command: {ctx.command.qualified_name}\n"
                f"Message: {ctx.message.content}\n"
                f"Invoker: {ctx.author}\n"
                f"Error ID: {in_db['id']}"
            )
            await self.error_webhook.send(traceback, embed=webhook_error_embed, username="Command Error")
            _log.error(f"Ignoring exception in command {ctx.command}:", exc_info=error)
            view = UnknownError(member=ctx.author, bot=self.bot, error_id=in_db["id"])
            view.message = await ctx.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
