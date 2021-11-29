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
from utils import AvimetryBot, AvimetryContext, Blacklisted, Maintenance, NotGuildOwner
from discord.ext import commands
from difflib import get_close_matches


class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message):
        return (message.channel.id, message.content)


class ErrorHandler(core.Cog):
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.blacklist_cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)
        self.maintenance_cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.channel)
        self.no_dm_command_cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)
        self.not_found_cooldown_content = CooldownByContent.from_cooldown(1, 15, commands.BucketType.user)
        self.not_found_cooldown = commands.CooldownMapping.from_cooldown(2, 30, commands.BucketType.user)
        self.error_webhook = discord.Webhook.from_url(
            self.bot.settings["webhooks"]["error_log"],
            session=self.bot.session,
        )
        self.beta_webhook = discord.Webhook.from_url(
            self.bot.settings["webhooks"]["error_log2"],
            session=self.bot.session,
        )

    def reset(self, ctx: AvimetryContext):
        try:
            ctx.command.reset_cooldown(ctx)
        except Exception:
            pass

    @core.Cog.listener()
    async def on_command_error(self, ctx: AvimetryContext, error):
        error = getattr(error, "original", error)
        if hasattr(ctx.command, 'on_error'):
            if not hasattr(ctx, 'eh'):
                return
        elif ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
            if not hasattr(ctx, 'eh'):
                return

        reinvoke = (
            commands.CommandOnCooldown,
            commands.NoPrivateMessage,
            commands.MaxConcurrencyReached,
            commands.MissingAnyRole,
            commands.MissingPermissions,
            commands.MissingRole,
            Maintenance,
            Blacklisted
        )
        if await self.bot.is_owner(ctx.author) and isinstance(error, reinvoke):
            try:
                return await ctx.reinvoke()
            except Exception:
                pass
        elif await self.bot.is_owner(ctx.author) and ctx.prefix == '' and isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, Blacklisted):
            blacklisted = discord.Embed(
                title=f"You are globally blacklisted from {self.bot.user.name}",
                description=(
                    f"Blacklist reason: `{error.reason}`\n"
                    "If you think this message is an error, "
                    "Please join the [support](https://discord.gg/muTVFgDvKf) server to appeal."
                ),
            )
            bucket = self.blacklist_cooldown.get_bucket(ctx.message)
            retry_after = bucket.update_rate_limit()
            if not retry_after:
                return await ctx.send(embed=blacklisted, delete_after=30)
            return

        if isinstance(error, Maintenance):
            bucket = self.maintenance_cooldown.get_bucket(ctx.message).update_rate_limit()
            if not bucket:
                return await ctx.send(f'{self.bot.user.name} has maintenance mode enabled. Try again later.')

        if isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(
                title="No DM commands",
                description="Commands do not work in DMs because I work best in servers."
            )
            bucket = self.no_dm_command_cooldown(ctx.message)
            retry_after = bucket.update_rate_limit()
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
                bucket1 = self.not_found_cooldown_content.get_bucket(ctx.message).update_rate_limit()
                bucket2 = self.not_found_cooldown.get_bucket(ctx.message).update_rate_limit()
                if not bucket1 or not bucket2:
                    conf = await ctx.confirm(embed=embed)
                    if conf.result:
                        if conf.result is False:
                            await ctx.message.delete()
                        new = copy.copy(ctx.message)
                        new._edited_timestamp = datetime.datetime.now(datetime.timezone.utc)
                        new.content = new.content.replace(ctx.invoked_with, match[0])
                        ctx = await self.bot.get_context(new)
                        try:
                            await self.bot.invoke(ctx)
                        except commands.CommandInvokeError:
                            await ctx.send("Something failed while trying to invoke. Try again?")

        elif isinstance(error, commands.CommandOnCooldown):
            rate = error.cooldown.rate
            per = error.cooldown.per
            cd_type = 'globally' if error.type.name == 'default' else f'per {error.type.name}'
            cd = discord.Embed(
                title="Slow down",
                description=(
                    f"This command can be used {rate} {'time' if rate == 1 else 'times'} "
                    f"every {per} seconds {cd_type}.\n"
                    f"Please try again in {error.retry_after:,.2f} seconds."
                )
            )
            return await ctx.send(embed=cd)

        elif isinstance(error, commands.MaxConcurrencyReached):
            max_uses = discord.Embed(
                title="Slow Down",
                description=(
                    f"This command has reached its max concurrency.\nIt can only be used {error.number} "
                    f"{'time' if error.number == 1 else 'times'} {error.per.name}."),
            )
            return await ctx.send(embed=max_uses)

        elif isinstance(error, commands.BotMissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]

            if len(missing) > 2:
                fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)

            bnp = discord.Embed(
                title="Missing Permissions",
                description=f"I need the following permissions to run this command:\n{fmt}"
            )
            try:
                await ctx.send(embed=bnp)
            except discord.HTTPException:
                return

        elif isinstance(error, commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_permissions]

            if len(missing) > 2:
                fmt = '{}, and `{}`'.format(", ".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)

            np = discord.Embed(
                title="Missing Permissions",
                description=f"You need the following permissions to run this command:\n{fmt}"
            )
            return await ctx.send(embed=np)

        elif isinstance(error, commands.NotOwner):
            no = discord.Embed(
                title="Missing Permissions",
                description="You do not own this bot."
            )
            return await ctx.send(embed=no)

        elif isinstance(error, NotGuildOwner):
            no = discord.Embed(
                title="Missing Permissions",
                description="You do not own this server."
            )
            return await ctx.send(embed=no)

        elif isinstance(error, commands.MissingRequiredArgument):
            self.reset(ctx)
            a = discord.Embed(
                title="Missing Arguments",
                description=(
                    f"`{error.param.name}` is a required parameter to run this command.\n"
                    f"Do you need help for `{ctx.command.qualified_name}`?"
                )
            )
            ctx.message._edited_timestamp = datetime.datetime.now(datetime.timezone.utc)
            conf = await ctx.confirm(embed=a, delete_after=True)
            if conf.result:
                return await ctx.send_help(ctx.command)
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(
                "This command is not enabled at the moment.")

        elif isinstance(error, commands.BadArgument):
            self.reset(ctx)
            ba = discord.Embed(
                title="Bad Argument",
                description=str(error),
            )
            return await ctx.send(embed=ba)

        elif isinstance(error, commands.BadUnionArgument):
            self.reset(ctx)
            bad_union_arg = discord.Embed(
                title="Bad Argument",
                description=error
            )
            return await ctx.send(embed=bad_union_arg)

        elif isinstance(error, commands.TooManyArguments):
            self.reset(ctx)
            many_arguments = discord.Embed(
                title="Too many arguments",
                description=str(error),
            )
            return await ctx.send(embed=many_arguments)

        elif isinstance(error, commands.ArgumentParsingError):
            embed = discord.Embed(
                title="Quote Error",
                description=error
            )
            return await ctx.send(embed=embed)

        else:
            self.reset(ctx)
            DefaultFormatter().theme["_ansi_enabled"] = False
            traceback = f"```{''.join(DefaultFormatter().format_exception(type(error), error, error.__traceback__))}```"
            if len(traceback) > 4096:
                traceback = f"Error was too long: {await self.bot.myst.post(traceback, 'bash')}"

            webhook_error_embed = discord.Embed(
                title="An error has occured",
                description=traceback,
            )
            error_embed = discord.Embed(title="An error has occured")

            query = "SELECT * FROM command_errors WHERE command=$1 and error=$2"
            check = await self.bot.pool.fetchrow(query, ctx.command.qualified_name, str(error))
            if not check:
                insert_query = (
                    "INSERT INTO command_errors (command, error) "
                    "VALUES ($1, $2) "
                    "RETURNING *"
                )
                insert = await self.bot.pool.fetchrow(insert_query, ctx.command.qualified_name, str(error))
                error_embed.description = (
                    "An unknown error was raised while running this command. The error has been logged and "
                    f"you can track this error using `{ctx.prefix}error {insert['id']}`\n\n"
                    f"Error:```py\n{error}```"
                )
                webhook_error_embed.add_field(
                    name="Error Info",
                    value=(
                        f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
                        f"Channel: {ctx.channel} ({ctx.channel.id})\n"
                        f"Command: {ctx.command.qualified_name}\n"
                        f"Message: {ctx.message.content}\n"
                        f"Invoker: {ctx.author}\n"
                        f"Error ID: {insert['id']}"
                    )
                )
            elif check["error"] == str(error):
                error_embed.description = (
                    "A known error was raised while running this command and hasn't been fixed.\n"
                    f"You can check the error status using `{ctx.prefix}error {check['id']}`\n\n"
                    f"Error:```py\n{error}```"
                )
            view = discord.ui.View(timeout=None)
            view.add_item(
                discord.ui.Button(style=discord.ButtonStyle.link, label="Support Server", url=self.bot.support)
            )
            await self.error_webhook.send(embed=webhook_error_embed, username="Command Error")
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            tb.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            await ctx.send(embed=error_embed, view=view)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
