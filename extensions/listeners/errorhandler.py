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
import copy
import logging
import traceback as tb

import discord
import humanize

import core
from core import Bot, Context
from core.exceptions import (
    Blacklisted,
    Maintenance,
    NotGuildOwner,
    CommandDisabledChannel,
    CommandDisabledGuild,
)
from utils import View, format_list
from discord.ext import commands
from difflib import get_close_matches


_log = logging.getLogger("avimetry")


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
        self.message = None
        self.cooldown = commands.CooldownMapping.from_cooldown(2, 60, commands.BucketType.user)

    async def interaction_check(self, interaction: discord.Interaction):
        return True

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None)

    @discord.ui.button(label="Track Error", style=discord.ButtonStyle.blurple)
    async def track_error(self, interaction: discord.Interaction, button: discord.Button):
        retry = self.cooldown.update_rate_limit(self.message)
        if retry:
            return await interaction.response.send_message(
                f"You are doing that too fast. Please try again in {retry:,.2f} seconds.",
                ephemeral=True,
            )
        check = await self.bot.pool.fetchrow("SELECT trackers FROM command_errors WHERE id = $1", self.error_id)
        if self.member.id in check["trackers"]:
            remove_tracker = "UPDATE command_errors SET trackers = ARRAY_REMOVE(trackers, $2) WHERE id = $1"
            await self.bot.pool.execute(remove_tracker, self.error_id, self.member.id)
            return await interaction.response.send_message(f"No longer tracking Error #{self.error_id}", ephemeral=True)
        add_tracker = "UPDATE command_errors SET trackers = ARRAY_APPEND(trackers, $2) WHERE id = $1"
        await self.bot.pool.execute(add_tracker, self.error_id, self.member.id)
        return await interaction.response.send_message(f"Now tracking Error #{self.error_id}.", ephemeral=True)


class ErrorHandler(core.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.blacklist_cooldown = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)
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

    def reset(self, ctx: Context):
        try:
            ctx.command.reset_cooldown(ctx)
        except Exception:
            pass

    def get_cooldown(self, command):
        try:
            rate = command._buckets._cooldown.rate
            cd_type = command._buckets.type.name
            per = humanize.precisedelta(command._buckets._cooldown.per)
            time = "times" if rate > 1 else "time"
            return f"{per} every {rate} {time} per {cd_type}"
        except AttributeError:
            return None

    @core.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        error = getattr(error, "original", error)

        cog_has_handler = ctx.cog.has_error_handler() if ctx.cog else None
        command_has_handler = ctx.command.has_error_handler() if ctx.command else None

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
        if (command_has_handler or cog_has_handler) and ctx.locally_handled is True:
            return

        if not ctx.channel.permissions_for(ctx.me).send_messages:
            return

        if await self.bot.is_owner(ctx.author) and isinstance(error, reinvoke):
            try:
                return await ctx.reinvoke(restart=True)
            except Exception:
                pass
        elif await self.bot.is_owner(ctx.author) and ctx.prefix == "" and isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, Blacklisted):
            blacklisted = Embed(
                title=f"You are blacklisted from {self.bot.user.name}",
                description=(f"Reason: `{error.reason}`\n" f"If you want to appeal, please join the support server."),
            )
            retry_after = self.blacklist_cooldown.update_rate_limit(ctx.message)
            if not retry_after:
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="Support Server", url=self.bot.support))
                return await ctx.send(embed=blacklisted, delete_after=30, view=view)
            return

        elif isinstance(error, Maintenance):
            retry_after = self.maintenance_cooldown.update_rate_limit(ctx.message)
            if not retry_after:
                return await ctx.send("Maintenance mode is enabled. Try again later.")
            return

        elif isinstance(error, commands.NoPrivateMessage):
            embed = Embed(
                title="No DM commands",
                description="Commands do not work in DMs because I work best in servers.",
            )
            retry_after = self.no_dm_command_cooldown.update_rate_limit()
            if not retry_after:
                return await ctx.send(embed=embed)
            return

        elif isinstance(error, commands.CommandNotFound):
            if ctx.author.id in ctx.cache.blacklist:
                return
            if cog := self.bot.get_cog(ctx.invoked_with):
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
            if match := get_close_matches(not_found, all_commands):
                embed = Embed(title="Invalid Command")
                embed.description = f'I couldn\'t find a command "{not_found}". Did you mean {match[0]}?'
                bucket1 = self.not_found_cooldown_content.update_rate_limit(ctx.message)
                bucket2 = self.not_found_cooldown.update_rate_limit(ctx.message)
                if not bucket1 or not bucket2:
                    conf = await ctx.confirm(embed=embed)
                    if conf.result:
                        new = copy.copy(ctx.message)
                        new._edited_timestamp = datetime.datetime.now(datetime.timezone.utc)
                        new.content = new.content.replace(ctx.invoked_with, match[0])
                        ctx = await self.bot.get_context(new)
                        await self.bot.invoke(ctx)
                    if conf.result is False:
                        return await conf.message.delete()

        elif isinstance(error, commands.CommandOnCooldown):
            cd = Embed(
                title="Slow down",
                description=(
                    "This command is on cooldown.\n"
                    f"Please try again in {error.retry_after:,.2f} seconds.\n"
                    f"Command cooldown: {self.get_cooldown(ctx.command)}"
                ),
            )
            return await ctx.send(embed=cd)

        elif isinstance(error, commands.MaxConcurrencyReached):
            max_uses = Embed(
                title="Slow Down",
                description=(
                    f"This can only be used {error.number} "
                    f"{'time' if error.number == 1 else 'times'} {error.per.name}."
                ),
            )
            return await ctx.send(embed=max_uses)

        elif isinstance(error, commands.BotMissingPermissions):
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
                await ctx.send(embed=bnp)
            except discord.HTTPException:
                return

        elif isinstance(error, commands.MissingPermissions):
            missing = [perm.replace("_", " ").replace("guild", "server").title() for perm in error.missing_permissions]

            if len(missing) > 2:
                fmt = f'{", ".join(missing[:-1])}, and `{missing[-1]}`'
            else:
                fmt = " and ".join(missing)

            np = Embed(
                title="Missing Permissions",
                description=f"You need the following permissions to run this command:\n{fmt}",
            )
            return await ctx.send(embed=np)

        elif isinstance(error, commands.NotOwner):
            no = Embed(title="Missing Permissions", description="You do not own this bot.")
            return await ctx.send(embed=no)

        elif isinstance(error, NotGuildOwner):
            no = Embed(title="Missing Permissions", description="You do not own this server.")
            return await ctx.send(embed=no)

        elif isinstance(error, commands.MissingRequiredArgument):
            self.reset(ctx)
            a = Embed(
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
            return await conf.message.delete()

        elif isinstance(error, CommandDisabledGuild):
            retry_after = self.disabled_command.update_rate_limit(ctx.message)
            if not retry_after:
                return await ctx.send("You can not use this command, It is disabled in this server.")

        elif isinstance(error, CommandDisabledChannel):
            retry_after = self.disabled_channel.update_rate_limit(ctx.message)
            if not retry_after:
                return await ctx.send("Commands have been disabled in this channel.")

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send("This command is not enabled at the moment.")

        elif isinstance(error, commands.BadArgument):
            self.reset(ctx)
            ba = Embed(
                title="Bad Argument",
                description=str(error),
            )
            return await ctx.send(embed=ba)

        elif isinstance(error, commands.BadUnionArgument):
            self.reset(ctx)
            bad_union_arg = Embed(title="Bad Argument", description=error)
            return await ctx.send(embed=bad_union_arg)

        elif isinstance(error, commands.BadLiteralArgument):
            self.reset(ctx)
            bad_literal_arg = Embed(
                title="Bad Argument",
                description=f"This argument must be:\n {format_list(error.literals, last='or')}.",
            )
            return await ctx.send(embed=bad_literal_arg)

        elif isinstance(error, commands.TooManyArguments):
            self.reset(ctx)
            many_arguments = Embed(
                title="Too many arguments",
                description=str(error),
            )
            return await ctx.send(embed=many_arguments)

        elif isinstance(error, commands.ArgumentParsingError):
            embed = Embed(title="Quote Error", description=error)
            return await ctx.send(embed=embed)

        else:
            self.reset(ctx)
            exc = tb.format_exception(type(error), error, error.__traceback__)
            traceback = f"```{''.join(exc)}```"
            if len(traceback) > 1995:
                traceback = f"Error was too long: {await self.bot.myst.post(traceback, 'bash')}"
            query = "SELECT * FROM command_errors WHERE command=$1 and error=$2"
            in_db = await self.bot.pool.fetchrow(query, ctx.command.qualified_name, str(error))
            if not in_db:
                insert_query = "INSERT INTO command_errors (command, error) " "VALUES ($1, $2) " "RETURNING *"
                inserted_error = await self.bot.pool.fetchrow(insert_query, ctx.command.qualified_name, str(error))
                embed = Embed(
                    title="An unknown error occured",
                    description=(
                        "This error has been logged and will be fixed soon.\n"
                        "You can track this error with the button below, or use "
                        f"`{ctx.prefix}error {inserted_error['id']}`.\n\n"
                        f"Error Information:```py\n{error}```"
                    ),
                )
            elif in_db["error"] == str(error):
                embed = Embed(
                    title="A known error occured",
                    description=(
                        "This error was already logged, but has not been fixed.\n"
                        "You can track this error with the button below, or use "
                        f"`{ctx.prefix}error {in_db['id']}`.\n\n"
                        f"Error Information:```py\n{error}```"
                    ),
                )
            webhook_error_embed = Embed(title="A new error" if not in_db else "Old error")
            error_info = in_db or inserted_error
            webhook_error_embed.description = (
                f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
                f"Channel: {ctx.channel} ({ctx.channel.id})\n"
                f"Command: {ctx.command.qualified_name}\n"
                f"Message: {ctx.message.content}\n"
                f"Invoker: {ctx.author}\n"
                f"Error ID: {error_info['id']}"
            )
            await self.error_webhook.send(traceback, embed=webhook_error_embed, username="Command Error")
            _log.error(f"Ignoring exception in command {ctx.command}:", exc_info=error)
            view = UnknownError(member=ctx.author, bot=self.bot, error_id=error_info["id"])
            view.message = await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
