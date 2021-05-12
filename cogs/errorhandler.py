import discord
import datetime
import prettify_exceptions
import humanize
from config import webhooks
from utils import AvimetryBot, AvimetryContext, Blacklisted
from discord.ext import commands
from difflib import get_close_matches


class ErrorHandler(commands.Cog):
    def __init__(self, avi):
        self.avi: AvimetryBot = avi
        self.cd_mapping = commands.CooldownMapping.from_cooldown(1, 300, commands.BucketType.user)
        self.error_webhook = discord.Webhook.from_url(
            webhooks["error_log"],
            adapter=discord.AsyncWebhookAdapter(self.avi.session)
        )

    def reset(self, ctx: AvimetryContext):
        try:
            ctx.command.reset_cooldown(ctx)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx: AvimetryContext, error):
        reinvoke = (
            commands.CommandOnCooldown,
            commands.MaxConcurrencyReached,
            commands.MissingAnyRole,
            commands.MissingPermissions,
            commands.MissingRole
        )
        if await self.avi.is_owner(ctx.author) and isinstance(error, reinvoke):
            return await ctx.reinvoke

        error = getattr(error, "original", error)

        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, Blacklisted):
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
                await ctx.send_error(embed=blacklisted, delete_after=15)

        elif isinstance(error, commands.CommandNotFound):
            if ctx.author.id in ctx.cache.blacklist:
                return
            not_found_embed = discord.Embed(title="Invalid Command")
            not_found = ctx.invoked_with
            match = "\n".join(
                get_close_matches(not_found, [i.name for i in ctx.bot.commands])
            )
            if match:
                not_found_embed.description = f'"{not_found}" was not found. Did you mean...\n`{match}`'
                not_found_embed.set_footer(
                    text=f"Use {ctx.clean_prefix}help to see the whole list of commands."
                )
                await ctx.send_error(embed=not_found_embed)

        elif isinstance(error, commands.CommandOnCooldown):
            cd = discord.Embed(
                title="Slow down",
                description=f"This command is on cooldown. Try again in {humanize.naturaldelta(error.retry_after)}."
            )
            await ctx.send_error(embed=cd)

        elif isinstance(error, commands.MaxConcurrencyReached):
            max_uses = discord.Embed(
                title="Slow Down",
                description=(
                    f"This command can only be used {error.number} "
                    f"{'time' if error.number == 1 else 'times'} per {error.per.name}."),
            )
            await ctx.send_error(embed=max_uses)

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
            await ctx.send_error(embed=bnp)

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
            await ctx.send_error(embed=np)

        elif isinstance(error, commands.NotOwner):
            no = discord.Embed(
                title="Missing Permissions",
                description="You do not own this bot."
            )
            await ctx.send_error(embed=no)

        elif isinstance(error, commands.MissingRequiredArgument):
            self.reset(ctx)
            a = discord.Embed(
                title="Missing Arguments",
                description=(
                    f"`{error.param.name}` is a required parameter to run this command.\n"
                    f"Send help for `{ctx.invoked_with}`?"
                )
            )
            conf = await ctx.confirm(embed=a)
            if conf:
                await ctx.send_help(ctx.command)
            return

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send_error(
                "This command is not enabled at the moment.")

        elif isinstance(error, commands.BadArgument):
            self.reset(ctx)
            ba = discord.Embed(
                title="Bad Argument",
                description=str(error),
            )
            await ctx.send_error(embed=ba)

        elif isinstance(error, commands.TooManyArguments):
            self.reset(ctx)
            many_arguments = discord.Embed(
                title="Too many arguments",
                description=str(error),
            )
            await ctx.send_error(embed=many_arguments)

        elif isinstance(error, commands.NoPrivateMessage):
            return
        else:
            self.reset(ctx)
            prettify_exceptions.DefaultFormatter().theme["_ansi_enabled"] = False
            exception = "".join(
                prettify_exceptions.DefaultFormatter().format_exception(
                    type(error), error, error.__traceback__
                )
            )
            print(exception)
            ee = discord.Embed(
                timestamp=datetime.datetime.utcnow()
            )
            myst_exception = await self.avi.myst.post(
                exception, syntax="python"
            )
            ee.title = "Unknown Error"
            ee.description = (
                "Uh oh, An uncaught error has occured. This normally shouldn't happen. "
                "The error was sent to the [support server](https://discord.gg/KaqqPhfwS4)."
                f"\n\n[Error]({myst_exception}):\n```py\n{error}```"
            )
            await ctx.send_error(embed=ee)
            embed = discord.Embed(
                title="Uncaught Error",
                description=f"```py\n {exception or myst_exception}```",
            )
            embed.add_field(
                name="Error Info",
                value=(
                    f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
                    f"Channel: {ctx.channel} ({ctx.channel.id})\n"
                    f"Command: {ctx.command.qualified_name}\n"
                    f"Message: {ctx.message.content}\n"
                    f"Invoker: {ctx.author}\n"
                )
            )
            await self.error_webhook.send(embed=embed, username="Error")


def setup(avi):
    avi.add_cog(ErrorHandler(avi))
