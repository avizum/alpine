"""
Cog for handling errors and unhandled errors
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


import discord
from discord.ext.commands.errors import CommandNotFound
import humanize
import sys
import traceback as tb

from prettify_exceptions import DefaultFormatter
from utils import AvimetryBot, AvimetryContext, Blacklisted, Maintenance
from discord.ext import commands
from difflib import get_close_matches


class ErrorHandler(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi
        self.cd_mapping = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)
        self.error_webhook = discord.Webhook.from_url(
            self.avi.settings["webhooks"]["error_log"],
            adapter=discord.AsyncWebhookAdapter(self.avi.session),
        )

    def reset(self, ctx: AvimetryContext):
        try:
            ctx.command.reset_cooldown(ctx)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx: AvimetryContext, error):
        error = getattr(error, "original", error)
        if hasattr(ctx.command, 'on_error'):
            return

        reinvoke = (
            commands.CommandOnCooldown,
            commands.NoPrivateMessage,
            commands.MaxConcurrencyReached,
            commands.MissingAnyRole,
            commands.MissingPermissions,
            commands.MissingRole,
            Maintenance
        )
        if await self.avi.is_owner(ctx.author) and isinstance(error, reinvoke):
            return await ctx.reinvoke()
        
        elif await self.avi.is_owner(ctx.author) and ctx.prefix == '' and isinstance(error, CommandNotFound):
            return

        elif isinstance(error, Blacklisted):
            blacklisted = discord.Embed(
                title=f"You are globally blacklisted from {self.avi.user.name}",
                description=(
                    f"Blacklist reason: `{error.reason}`\n"
                    "If you think this message is an error, "
                    "Please join the [support](https://discord.gg/KaqqPhfwS4) server to appeal."
                ),
            )
            bucket = self.cd_mapping.get_bucket(ctx.message)
            retry_after = bucket.update_rate_limit()
            if not retry_after:
                return await ctx.send(embed=blacklisted, delete_after=60)
        
        if isinstance(error, Maintenance):
            return await ctx.send('Maintenance mode enabled. Please try again later')

        elif isinstance(error, commands.CommandNotFound):
            if ctx.author.id in ctx.cache.blacklist:
                return
            not_found_embed = discord.Embed(title="Invalid Command")
            not_found = ctx.invoked_with
            all_commands = []
            for cmd in self.avi.commands:
                try:
                    await cmd.can_run(ctx)
                    all_commands.append(cmd.name)
                except commands.CommandError:
                    continue
            match = "\n".join(
                get_close_matches(not_found, all_commands)
            )
            if match:
                not_found_embed.description = f'"{not_found}" was not found. Did you mean...\n`{match}`'
                not_found_embed.set_footer(
                    text=f"Use {ctx.clean_prefix}help to see the whole list of commands."
                )
                await ctx.send(embed=not_found_embed)

        elif isinstance(error, commands.CommandOnCooldown):
            rate = error.cooldown.rate
            per = error.cooldown.per
            cd_type = str(error.cooldown.type).replace("BucketType.", "")
            cd = discord.Embed(
                title="Slow down",
                description=(
                    f"This command has reached its cooldown. It can be used {rate} {'time' if rate == 1 else 'times'} "
                    f"every {per} seconds per {cd_type}.\n"
                    f"Try again in {humanize.naturaldelta(error.retry_after)}."
                )
            )
            return await ctx.send(embed=cd)

        elif isinstance(error, commands.MaxConcurrencyReached):
            max_uses = discord.Embed(
                title="Slow Down",
                description=(
                    f"This command has reached its max concurrency.\nIt can only be used {error.number} "
                    f"{'time' if error.number == 1 else 'times'} per {error.per.name}."),
            )
            return await ctx.send(embed=max_uses)

        elif isinstance(error, commands.BotMissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]

            if len(missing) > 2:
                fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)

            bnp = discord.Embed(
                title="Missing Permissions",
                description=f"I need the following permissions to run this command:\n{fmt}"
            )
            return await ctx.send(embed=bnp)

        elif isinstance(error, commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]

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
                description="You do not own this bot. Stay away"
            )
            return await ctx.send(embed=no)

        elif isinstance(error, commands.MissingRequiredArgument):
            self.reset(ctx)
            a = discord.Embed(
                title="Missing Arguments",
                description=(
                    f"`{error.param.name}` is a required parameter to run this command.\n"
                    f"Do you need help for `{ctx.invoked_with}`?"
                )
            )
            conf = await ctx.confirm(embed=a)
            if conf:
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

        elif isinstance(error, commands.NoPrivateMessage):
            return
        else:
            self.reset(ctx)
            DefaultFormatter().theme["_ansi_enabled"] = False
            traceback = (
                "".join(DefaultFormatter().format_exception(type(error), error, error.__traceback__))
            )
            if len(traceback) > 2000:
                traceback = f"Error was too long: {await self.avi.myst.post(traceback, 'bash')}"

            webhook_error_embed = discord.Embed(
                title="An error has occured",
                description=f"```py\n{traceback}```",
            )
            error_embed = discord.Embed(title="An error has occured")

            query = "SELECT * FROM command_errors WHERE command=$1 and error=$2"
            check = await self.avi.pool.fetchrow(query, ctx.command.qualified_name, str(error))
            if not check:
                insert_query = (
                    "INSERT INTO command_errors (command, error) "
                    "VALUES ($1, $2) "
                    "RETURNING *"
                )
                insert = await self.avi.pool.fetchrow(insert_query, ctx.command.qualified_name, str(error))
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
                    )
                )
            elif check["error"] == str(error):
                error_embed.description = (
                    "A known error was raised while running this command and hasn't been fixed.\n"
                    f"You can check the error status using `{ctx.prefix}error {check['id']}`\n\n"
                    f"Error:```py\n{error}```"
                )
            await ctx.send(embed=error_embed)
            await self.error_webhook.send(embed=webhook_error_embed, username="Command Error")
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            tb.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(avi):
    avi.add_cog(ErrorHandler(avi))
