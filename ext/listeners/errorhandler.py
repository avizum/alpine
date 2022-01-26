"""
Cog for handling errors and unhandled errors
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

import datetime
import discord
import sys
import traceback as tb
import core
import copy

from prettify_exceptions import DefaultFormatter
from utils import (
    AvimetryBot,
    AvimetryContext,
    Blacklisted,
    Maintenance,
    NotGuildOwner,
    CommandDisabledGuild,
    CommandDisabledChannel,
    AvimetryView
)
from discord.ext import commands
from difflib import get_close_matches


class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message):
        return (message.channel.id, message.content)


class UnknownError(AvimetryView):
    def __init__(self, *, member: discord.Member, bot: AvimetryBot, error_id: int):
        self.error_id = error_id
        self.bot = bot
        super().__init__(member=member, timeout=3600)
        support = discord.ui.Button(style=discord.ButtonStyle.link, label="Support Server", url=self.bot.support)
        self.add_item(support)
        self.cooldown = commands.CooldownMapping.from_cooldown(2, 60, commands.BucketType.user)

    async def interaction_check(self, interaction: discord.Interaction):
        return True

    async def on_timeout(self) -> None:
        await self.message.edit(view=None)

    @discord.ui.button(label="Track Error", style=discord.ButtonStyle.blurple)
    async def track_error(self, button: discord.Button, interaction: discord.Interaction):
        retry = self.cooldown.update_rate_limit(self.message)
        if retry:
            return await interaction.response.send_message(
                f"You are doing that too fast. Please try again in {retry:,.2f} seconds.", ephemeral=True
            )
        check = await self.bot.pool.fetchrow("SELECT trackers FROM command_errors WHERE id = $1", self.error_id)
        if self.member.id in check['trackers']:
            remove_tracker = "UPDATE command_errors SET trackers = ARRAY_REMOVE(trackers, $2) WHERE id = $1"
            await self.bot.pool.execute(remove_tracker, self.error_id, self.member)
            return await interaction.response.send_message(f"No longer tracking Error #{self.error_id}", ephemeral=True)
        add_tracker = "UPDATE command_errors SET trackers = ARRAY_APPEND(trackers, $2) WHERE id = $1"
        await self.bot.pool.execute(add_tracker, self.error_id, self.member)
        return await interaction.response.send_message(f"Now tracking Error #{self.error_id}.", ephemeral=True)


class ErrorHandler(core.Cog):
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.blacklist_cooldown = commands.CooldownMapping.from_cooldown(
            1, 300, commands.BucketType.user
        )
        self.maintenance_cooldown = commands.CooldownMapping.from_cooldown(
            1, 300, commands.BucketType.channel
        )
        self.no_dm_command_cooldown = commands.CooldownMapping.from_cooldown(
            1, 300, commands.BucketType.user
        )
        self.not_found_cooldown_content = CooldownByContent.from_cooldown(
            1, 15, commands.BucketType.user
        )
        self.not_found_cooldown = commands.CooldownMapping.from_cooldown(
            2, 30, commands.BucketType.user
        )
        self.disabled_channel = commands.CooldownMapping.from_cooldown(
            1, 60, commands.BucketType.channel
        )
        self.disabled_command = commands.CooldownMapping.from_cooldown(
            1, 60, commands.BucketType.channel
        )
        self.error_webhook = discord.Webhook.from_url(
            self.bot.settings["webhooks"]["error_log"],
            session=self.bot.session,
        )

    def reset(self, ctx: AvimetryContext):
        try:
            ctx.command.reset_cooldown(ctx)
        except Exception:
            pass

    @core.Cog.listener()
    async def on_command_error(self, ctx: AvimetryContext, error: commands.CommandError):
        error = getattr(error, "original", error)
        if hasattr(ctx.command, "on_error"):
            if not hasattr(ctx, "eh"):
                return
        elif (
            ctx.cog
            and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None
        ):
            if not hasattr(ctx, "eh"):
                return

        reinvoke = (
            commands.CommandOnCooldown,
            commands.NoPrivateMessage,
            commands.MaxConcurrencyReached,
            commands.MissingAnyRole,
            commands.MissingPermissions,
            commands.MissingRole,
            commands.DisabledCommand,
            Maintenance,
            Blacklisted,
        )
        if await self.bot.is_owner(ctx.author) and isinstance(error, reinvoke):
            try:
                return await ctx.reinvoke()
            except Exception:
                pass
        elif (
            await self.bot.is_owner(ctx.author)
            and ctx.prefix == ""
            and isinstance(error, commands.CommandNotFound)
        ):
            return

        elif isinstance(error, Blacklisted):
            blacklisted = discord.Embed(
                title=f"You are blacklisted from {self.bot.user.name}",
                description=(
                    f"Reason: `{error.reason}`\n"
                    f"If you want to appeal, please join the support server."
                ),
            )
            retry_after = self.blacklist_cooldown.update_rate_limit(ctx.message)
            if not retry_after:
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Support Server", url=self.bot.support))
                return await ctx.send(embed=blacklisted, delete_after=30, view=view)
            return

        if isinstance(error, Maintenance):
            retry_after = self.maintenance_cooldown.update_rate_limit(ctx.message)
            if not retry_after:
                return await ctx.send("Maintenance mode is enabled. Try again later.")
            return

        if isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(
                title="No DM commands",
                description="Commands do not work in DMs because I work best in servers.",
            )
            retry_after = self.no_dm_command_cooldown.update_rate_limit()
            if not retry_after:
                return await ctx.semd(embed=embed)
            return

        elif isinstance(error, commands.CommandNotFound):
            if ctx.author.id in ctx.cache.blacklist:
                return
            cog = self.bot.get_cog(ctx.invoked_with)
            if cog:
                return await ctx.send_help(cog)
            not_found = ctx.invoked_with
            all_commands = []
            for cmd in self.bot.commands:
                try:
                    await cmd.can_run(ctx)
                    all_commands.append(cmd.name)
                    if cmd.aliases:
                        all_commands.extend(cmd.aliases)
                except commands.CommandError:
                    continue
            match = get_close_matches(not_found, all_commands)
            if match:
                embed = discord.Embed(title="Invalid Command")
                embed.description = f'I couldn\'t find a command "{not_found}". Did you mean {match[0]}?'
                bucket1 = self.not_found_cooldown_content.update_rate_limit(ctx.message)
                bucket2 = self.not_found_cooldown.update_rate_limit(ctx.message)
                if not bucket1 or not bucket2:
                    conf = await ctx.confirm(embed=embed)
                    if conf.result:
                        new = copy.copy(ctx.message)
                        new._edited_timestamp = datetime.datetime.now(
                            datetime.timezone.utc
                        )
                        new.content = new.content.replace(ctx.invoked_with, match[0])
                        ctx = await self.bot.get_context(new)
                        try:
                            await self.bot.invoke(ctx)
                        except commands.CommandInvokeError:
                            await ctx.send(
                                "Something failed while trying to invoke. Try again?"
                            )
                    if conf.result is False:
                        return await conf.message.delete()

        elif isinstance(error, commands.CommandOnCooldown):
            cd = discord.Embed(
                title="Slow down",
                description=(
                    "This command is on cooldown.\n"
                    f"Please try again in {error.retry_after:,.2f} seconds."
                ),
            )
            return await ctx.send(embed=cd)

        elif isinstance(error, commands.MaxConcurrencyReached):
            max_uses = discord.Embed(
                title="Slow Down",
                description=(
                    f"This can only be used {error.number} "
                    f"{'time' if error.number == 1 else 'times'} {error.per.name}."
                ),
            )
            return await ctx.send(embed=max_uses)

        elif isinstance(error, commands.BotMissingPermissions):
            missing = [
                perm.replace("_", " ").replace("guild", "server").title()
                for perm in error.missing_permissions
            ]

            if len(missing) > 2:
                fmt = "{}, and {}".format(", ".join(missing[:-1]), missing[-1])
            else:
                fmt = " and ".join(missing)

            bnp = discord.Embed(
                title="Missing Permissions",
                description=f"I need the following permissions to run this command:\n{fmt}",
            )
            try:
                await ctx.send(embed=bnp)
            except discord.HTTPException:
                return

        elif isinstance(error, commands.MissingPermissions):
            missing = [
                perm.replace("_", " ").replace("guild", "server").title()
                for perm in error.missing_permissions
            ]

            if len(missing) > 2:
                fmt = "{}, and `{}`".format(", ".join(missing[:-1]), missing[-1])
            else:
                fmt = " and ".join(missing)

            np = discord.Embed(
                title="Missing Permissions",
                description=f"You need the following permissions to run this command:\n{fmt}",
            )
            return await ctx.send(embed=np)

        elif isinstance(error, commands.NotOwner):
            no = discord.Embed(
                title="Missing Permissions", description="You do not own this bot."
            )
            return await ctx.send(embed=no)

        elif isinstance(error, NotGuildOwner):
            no = discord.Embed(
                title="Missing Permissions", description="You do not own this server."
            )
            return await ctx.send(embed=no)

        elif isinstance(error, commands.MissingRequiredArgument):
            self.reset(ctx)
            a = discord.Embed(
                title="Missing Arguments",
                description=(
                    f"`{error.param.name}` is a required parameter to run this command.\n"
                    f"Do you need help for `{ctx.command.qualified_name}`?"
                ),
            )
            ctx.message._edited_timestamp = datetime.datetime.now(datetime.timezone.utc)
            conf = await ctx.confirm(embed=a, delete_after=False)
            if conf.result:
                return await ctx.send_help(ctx.command)
            return

        elif isinstance(error, CommandDisabledGuild):
            retry_after = self.disabled_command.update_rate_limit(ctx.message)
            if not retry_after:
                return await ctx.send(
                    "You can not use this command, It is disabled in this server."
                )

        elif isinstance(error, CommandDisabledChannel):
            retry_after = self.disabled_channel.update_rate_limit(ctx.message)
            if not retry_after:
                return await ctx.send("Commands have been disabled in this channel.")

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send("This command is not enabled at the moment.")

        elif isinstance(error, commands.BadArgument):
            self.reset(ctx)
            ba = discord.Embed(
                title="Bad Argument",
                description=str(error),
            )
            return await ctx.send(embed=ba)

        elif isinstance(error, commands.BadUnionArgument):
            self.reset(ctx)
            bad_union_arg = discord.Embed(title="Bad Argument", description=error)
            return await ctx.send(embed=bad_union_arg)

        elif isinstance(error, commands.TooManyArguments):
            self.reset(ctx)
            many_arguments = discord.Embed(
                title="Too many arguments",
                description=str(error),
            )
            return await ctx.send(embed=many_arguments)

        elif isinstance(error, commands.ArgumentParsingError):
            embed = discord.Embed(title="Quote Error", description=error)
            return await ctx.send(embed=embed)

        else:
            self.reset(ctx)
            DefaultFormatter().theme["_ansi_enabled"] = False
            traceback = f"```{''.join(DefaultFormatter().format_exception(type(error), error, error.__traceback__))}```"
            if len(traceback) > 4096:
                traceback = (
                    f"Error was too long: {await self.bot.myst.post(traceback, 'bash')}"
                )

            query = "SELECT * FROM command_errors WHERE command=$1 and error=$2"
            in_db = await self.bot.pool.fetchrow(
                query, ctx.command.qualified_name, str(error)
            )
            if not in_db:
                insert_query = (
                    "INSERT INTO command_errors (command, error) "
                    "VALUES ($1, $2) "
                    "RETURNING *"
                )
                inserted_error = await self.bot.pool.fetchrow(
                    insert_query, ctx.command.qualified_name, str(error)
                )
                embed = discord.Embed(
                    title="An unknown error occured",
                    description=(
                        "This error has been logged and will be fixed soon.\n"
                        "You can track this error with the button below, or use "
                        f"`{ctx.prefix}error {inserted_error['id']}`.\n\n"
                        f"Error Information:```py\n{error}```"
                    )
                )
            elif in_db["error"] == str(error):
                embed = discord.Embed(
                    title="A known error occured",
                    description=(
                        "This error was already logged, but has not been fixed.\n"
                        "You can track this error with the button below, or use "
                        f"`{ctx.prefix}error {in_db['id']}`.\n\n"
                        f"Error Information:```py\n{error}```"
                    )
                )
            webhook_error_embed = discord.Embed(
                title="A new error" if not in_db else "Old error, Fix soon",
                description=traceback,
            )
            error_info = in_db or inserted_error
            webhook_error_embed.add_field(
                    name="Error Info",
                    value=(
                        f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
                        f"Channel: {ctx.channel} ({ctx.channel.id})\n"
                        f"Command: {ctx.command.qualified_name}\n"
                        f"Message: {ctx.message.content}\n"
                        f"Invoker: {ctx.author}\n"
                        f"Error ID: {error_info['id']}"
                    ),
                )
            await self.error_webhook.send(
                embed=webhook_error_embed, username="Command Error"
            )
            print(
                "Ignoring exception in command {}:".format(ctx.command), file=sys.stderr
            )
            tb.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            view = UnknownError(member=ctx.author, bot=self.bot, error_id=error_info['id'])
            view.message = await ctx.send(embed=embed, view=view)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
