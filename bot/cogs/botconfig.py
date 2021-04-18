import discord
import datetime
import psutil
import humanize
from discord.ext import commands
from utils.converters import Prefix
from utils.context import AvimetryContext


class BotInfo(commands.Cog, name="Utility"):
    def __init__(self, avi):
        self.avi = avi

# Mention prefix
    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.avi.get_context(message, cls=AvimetryContext)
        if message.author == self.avi.user:
            return
        if message.content == f"<@!{self.avi.user.id}>":
            prefix = self.avi.get_command("prefix")
            await prefix(ctx)

    @commands.command()
    async def prefix(self, ctx: AvimetryContext):
        command = self.avi.get_command("settings prefix")
        await command(ctx)

# Config Command
    @commands.group(
        invoke_without_command=True,
        brief="The base config command, use this configure settings",
        aliases=["config", "configuration"]
    )
    async def settings(self, ctx: AvimetryContext):
        await ctx.send_help("config")

# Config Prefix Commnad
    @settings.group(
        brief="Show all the prefixes of this server",
        invoke_without_command=True,
        name="prefix")
    async def settings_prefix(self, ctx: AvimetryContext):
        prefix = await ctx.cache.get_guild_settings(ctx.guild.id)
        if not prefix["prefixes"]:
            return await ctx.send("You don't have a custom prefix set yet. The default prefix is always `a.`")
        else:
            guild_prefix = prefix["prefixes"]
        if len(guild_prefix) == 1:
            return await ctx.send(f"The prefix for this server is `{guild_prefix[0]}`")
        await ctx.send(f"Here are my prefixes for this server: \n`{'` | `'.join(guild_prefix)}`")

    @settings_prefix.command(
        brief="Add a prefix to the server.",
        help="settings prefix add <prefix>",
        name="add"
    )
    @commands.has_permissions(administrator=True)
    async def prefix_add(self, ctx: AvimetryContext, prefix: Prefix):
        await self.avi.pool.execute(
            "UPDATE guild_settings SET prefixes = ARRAY_APPEND(prefixes, $2) WHERE guild_id = $1",
            ctx.guild.id, prefix)
        ctx.cache.guild_settings_cache[ctx.guild.id]["prefixes"].append(prefix)
        await ctx.send(f"Appended `{prefix}` to the list of prefixes.")

    @settings_prefix.command(
        brief="Remove a prefix from the list",
        name="remove"
    )
    @commands.has_permissions(administrator=True)
    async def prefix_remove(self, ctx: AvimetryContext, prefix):
        prefix = prefix.lower()
        guild_cache = await ctx.cache.get_guild_settings(ctx.guild.id)
        if not guild_cache:
            return await ctx.send(
                "You don't have any prefixes set for this server. Set one by using `a.settings prefix add <prefix>`"
            )

        guild_prefix = guild_cache["prefixes"]
        if prefix not in guild_prefix:
            return await ctx.send(f"`{prefix}` is not a prefix of this server.")

        await self.avi.pool.execute(
            "UPDATE guild_settings SET prefixes = ARRAY_REMOVE(prefixes, $2) WHERE guild_id = $1",
            ctx.guild.id, prefix)

        self.avi.temp.guild_settings_cache[ctx.guild.id]["prefixes"].remove(prefix)
        await ctx.send(f"Removed `{prefix}` from the list of prefixes")

    @settings.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def muterole(self, ctx: AvimetryContext, role: discord.Role):
        await self.avi.pool.execute(
            "UPDATE guild_settings SET mute_role = $1 WHERE guild_id = $2",
            role.id, ctx.guild.id)
        self.avi.temp.guild_settings_cache[ctx.guild.id]["mute_role"] = role.id
        for channel in ctx.guild.channels:
            perms = channel.overwrites_for(role)
            perms.update(send_messages=False)
            await channel.set_permissions(
                target=role,
                overwrite=perms,
                reason=f"Mute role set to {role.name} by {ctx.author}"
            )
        await ctx.send(f"Set the mute role to {role.mention}")

    @settings.group(invoke_without_command=True, brief="Configure logging")
    @commands.has_permissions(administrator=True)
    async def logging(self, ctx: AvimetryContext):
        await ctx.send_help("config logging")

    @logging.command(name="channel", brief="Configure logging channel")
    @commands.has_permissions(administrator=True)
    async def _channel(self, ctx: AvimetryContext, channel: discord.TextChannel):
        await self.avi.logs.upsert(
            {"_id": ctx.guild.id, "logging_channel": channel.id}
        )
        await ctx.send(f"Set logging channel to {channel}")

    @logging.command(brief="Configure delete logging")
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx: AvimetryContext, toggle: bool):
        await self.avi.logs.upsert({"_id": ctx.guild.id, "delete_log": toggle})
        await ctx.send(f"Set on_message_delete logs to {toggle}")

    @logging.command(brief="Configure edit logging")
    @commands.has_permissions(administrator=True)
    async def edit(self, ctx: AvimetryContext, toggle: bool):
        await self.avi.logs.upsert({"_id": ctx.guild.id, "edit_log": toggle})
        await ctx.send(f"Set on_message_edit logs to {toggle}")

    # Config Verification Command
    @settings.group(
        brief="Verify system configuration for this server",
        invoke_without_command=True,
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def verify(self, ctx: AvimetryContext, toggle: bool = None):
        if toggle is None:
            return await ctx.send_help("settings verify")
        await self.avi.config.upsert(
            {"_id": ctx.guild.id, "verification_gate": toggle}
        )
        await ctx.send(f"Set verify system is set to {toggle}")

    @verify.command(
        brief="Set the role to give when a member finishes verification."
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def role(self, ctx: AvimetryContext, role: discord.Role):
        await self.avi.config.upsert({"_id": ctx.guild.id, "gate_role": role.id})
        await ctx.send(f"The verify role is set to {role}")

    # Config Counting Command
    @settings.group(invoke_without_command=True, brief="Configure counting settings")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def counting(self, ctx: AvimetryContext):
        await ctx.send_help("config counting")

    @counting.command(brief="Set the count in the counting channel")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def setcount(self, ctx: AvimetryContext, count: int):
        await self.avi.config.upsert({"_id": ctx.guild.id, "current_count": count})
        await ctx.send(f"Set the count to {count}")

    @counting.command(brief="Set the channel for counting")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def channel(self, ctx: AvimetryContext, channel: discord.TextChannel):
        await self.avi.config.upsert(
            {"_id": ctx.guild.id, "counting_channel": channel.id}
        )
        await ctx.send(f"Set the counting channel to {channel}")

    # Bot Info Command
    @commands.command()
    async def about(self, ctx: AvimetryContext):
        embed = discord.Embed(title="Info about Avimetry")
        embed.add_field(name="Developer", value="avi#8771")
        embed.add_field(name="Ping", value=f"`{round(self.avi.latency * 1000)}ms`")
        embed.add_field(name="Guild Count", value=f"{len(self.avi.guilds)} Guilds")
        embed.add_field(name="User Count", value=f"{len(self.avi.users)} Users")
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent(interval=None)}%")
        embed.add_field(name="RAM Usage", value=f"{psutil.virtual_memory().percent}%")
        embed.add_field(
            name="Bot Invite",
            value=f"[here]({self.avi.invite})",
        )
        embed.add_field(name="Commands", value=len(self.avi.commands))
        embed.add_field(name="Commands ran", value=self.avi.commands_ran)
        embed.set_thumbnail(url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    # Uptime Command
    @commands.command(brief="Get the bot's uptime")
    async def uptime(self, ctx: AvimetryContext):
        delta_uptime = datetime.datetime.utcnow() - self.avi.launch_time
        ue = discord.Embed(
            title="Current Uptime",
            description=humanize.precisedelta(delta_uptime, format="%.2g"),
        )
        await ctx.send(embed=ue)

    # Ping Command
    @commands.command(brief="Gets the bot's ping.")
    async def ping(self, ctx: AvimetryContext):
        ping_embed = discord.Embed(title="🏓 Pong!")
        ping_embed.add_field(
            name="Websocket Latency",
            value=f"`{round(self.avi.latency * 1000)}ms`",
            inline=False,
        )
        ping_embed.add_field(
            name="API Latency",
            value=f"`{await self.avi.api_latency(ctx)}ms`",
            inline=False,
        )
        ping_embed.add_field(
            name="Database Latency (Mongo)",
            value=f"`{await self.avi.database_latency(ctx)}ms`",
            inline=False,
        )
        ping_embed.add_field(
            name="Database Latency (PostgreSQL)",
            value=f"`{await self.avi.postgresql_latency()}ms`",
            inline=False,
        )

        await ctx.send(embed=ping_embed)

    # Source Command
    # Follow the license, Thanks. If you do use this code, you have to make your bot's source public.
    @commands.command(brief="Sends the bot's source")
    async def source(self, ctx: AvimetryContext):
        source_embed = discord.Embed(
            title=f"{self.avi.user.name}'s source code",
            timestamp=datetime.datetime.utcnow(),
        )
        if self.avi.user.id != 756257170521063444:
            source_embed.description = "This bot is made by [avi](https://discord.com/users/750135653638865017). \
                It is run off of this [source code](https://github.com/avimetry/avimetry).\nKeep the license in mind"
        else:
            source_embed.description = (
                "Here is my [source code](https://github.com/avimetry/avimetry) made by "
                "[avi](https://discord.com/users/750135653638865017).\nMake sure you follow the license."
            )
        await ctx.send(embed=source_embed)

    # Invite Command
    @commands.group(invoke_without_command=True)
    async def invite(self, ctx: AvimetryContext):
        invite_embed = discord.Embed(
            title=f"{self.avi.user.name} Invite",
            description=(
                "Invite me to your server! Here is the invite link.\n"
                f"[Here]({str(discord.utils.oauth_url(self.avi.user.id, discord.Permissions(2147483647)))}) "
                "is the invite link."
            ),
        )
        invite_embed.set_thumbnail(url=self.avi.user.avatar_url)
        await ctx.send(embed=invite_embed)

    @invite.command()
    async def bot(self, ctx: AvimetryContext, bot: discord.Member):
        bot_invite = discord.Embed()
        bot_invite.set_thumbnail(url=bot.avatar_url)
        bot_invite.title = f"{bot.name} Invite"
        if bot.bot:
            bot_invite.description = (
                f"Invite {bot.name} to your server! Here is the invite link.\n"
                f"Click [here]({str(discord.utils.oauth_url(bot.id, discord.Permissions(2147483647)))}) for the invite!"
            )
        else:
            bot_invite.description = "That is not a bot. Make sure you mention a bot."
        await ctx.send(embed=bot_invite)

    @commands.command(brief="Request a feature to be added to the bot.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def request(self, ctx: AvimetryContext, *, request):
        request_channel = self.avi.get_channel(817093957322407956)
        req_send = discord.Embed(
            title=f"Request from {str(ctx.author)}",
            description=f"```{request}```"
        )
        await request_channel.send(embed=req_send)
        req_embed = discord.Embed(
            title="Request sent",
            description=(
                "Thank you for your request! Join the [support]('https://discord.gg/yCUtp2RcKs') server to see if \n"
                "your request has been approved.\n"
                "Please note that spam requests will get you permanently blacklisted from this bot."
            )
        )
        req_embed.add_field(
            name="Your \"useful\" request",
            value=f"```{request}```"
        )
        await ctx.send(embed=req_embed)


def setup(avi):
    avi.add_cog(BotInfo((avi)))
