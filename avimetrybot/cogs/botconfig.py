import discord
import datetime
from discord.ext import commands
import psutil
import humanize


class BotInfo(commands.Cog, name="Utility"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

# Mention prefix
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avimetry.user:
            return
        if message.content == "<@!756257170521063444>":
            cool = await self.avimetry.config.find(message.guild.id)
            await message.channel.send(
                f"Hey {message.author.mention}, the prefix for **{message.guild.name}** is `{cool['prefix']}`"
            )

# Config Command
    @commands.group(
        invoke_without_command=True,
        brief="The base config command, use this configure settings",
        aliases=["config", "configuration"]
    )
    async def settings(self, ctx):
        await ctx.send_help("config")

# Config Prefix Commnad
    @settings.command(brief="Change the prefix of this server")
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, new_prefix):
        await self.avimetry.config.upsert({"_id": ctx.guild.id, "prefix": new_prefix})
        cp = discord.Embed(
            title="Set Prefix",
            description=f"The prefix for **{ctx.guild.name}** is now `{new_prefix}`"
        )
        await ctx.send(embed=cp)

    @settings.group(invoke_without_command=True, brief="Configure logging")
    @commands.has_permissions(administrator=True)
    async def logging(self, ctx):
        await ctx.send_help("config logging")

    @logging.command(name="channel", brief="Configure logging channel")
    @commands.has_permissions(administrator=True)
    async def _channel(self, ctx, channel: discord.TextChannel):
        await self.avimetry.logs.upsert(
            {"_id": ctx.guild.id, "logging_channel": channel.id}
        )
        await ctx.send(f"Set logging channel to {channel}")

    @logging.command(brief="Configure delete logging")
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx, toggle: bool):
        await self.avimetry.logs.upsert({"_id": ctx.guild.id, "delete_log": toggle})
        await ctx.send(f"Set on_message_delete logs to {toggle}")

    @logging.command(brief="Configure edit logging")
    @commands.has_permissions(administrator=True)
    async def edit(self, ctx, toggle: bool):
        await self.avimetry.logs.upsert({"_id": ctx.guild.id, "edit_log": toggle})
        await ctx.send(f"Set on_message_edit logs to {toggle}")

    # Config Verification Command
    @settings.group(
        brief="Verify system configuration for this server",
        invoke_without_command=True,
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def verify(self, ctx):
        await ctx.send_help("config verify")

    @verify.command(brief="Toggle the verification gate")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def toggle(self, ctx, bool: bool):
        await self.avimetry.config.upsert(
            {"_id": ctx.guild.id, "verification_gate": bool}
        )
        await ctx.send(f"Verification Gate is now {bool}")

    @verify.command(
        brief="Set the role to give when a member finishes verification."
    )
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def role(self, ctx, role: discord.Role):
        await self.avimetry.config.upsert({"_id": ctx.guild.id, "gate_role": role.id})
        await ctx.send(f"The verify role is set to {role}")

    # Config Counting Command
    @settings.group(invoke_without_command=True, brief="Configure counting settings")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def counting(self, ctx):
        await ctx.send_help("config counting")

    @counting.command(brief="Set the count in the counting channel")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def setcount(self, ctx, count: int):
        await self.avimetry.config.upsert({"_id": ctx.guild.id, "current_count": count})
        await ctx.send(f"Set the count to {count}")

    @counting.command(brief="Set the channel for counting")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        await self.avimetry.config.upsert(
            {"_id": ctx.guild.id, "counting_channel": channel.id}
        )
        await ctx.send(f"Set the counting channel to {channel}")

    # Bot Info Command
    @commands.command()
    async def about(self, ctx):
        embed = discord.Embed(title="Info about Avimetry")
        embed.add_field(name="Developer", value="avi#4927")
        embed.add_field(name="Ping", value=f"`{round(self.avimetry.latency * 1000)}ms`")
        embed.add_field(name="Guild Count", value=f"{len(self.avimetry.guilds)} Guilds")
        embed.add_field(name="User Count", value=f"{len(self.avimetry.users)} Users")
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent(interval=None)}%")
        embed.add_field(name="RAM Usage", value=f"{psutil.virtual_memory().percent}%")
        embed.add_field(
            name="Bot Invite",
            value=f"[here](f{str(discord.utils.oauth_url(self.avimetry.user.id, discord.Permissions(2147483647)))})",
        )
        embed.add_field(name="Commands", value=len(self.avimetry.commands))
        embed.add_field(name="Commands ran", value=self.avimetry.commands_ran)
        embed.set_thumbnail(url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    # Uptime Command
    @commands.command(brief="Get the bot's uptime")
    async def uptime(self, ctx):
        delta_uptime = datetime.datetime.utcnow() - self.avimetry.launch_time
        ue = discord.Embed(
            title="Current Uptime",
            description=humanize.precisedelta(delta_uptime, format="%.2g"),
        )
        await ctx.send(embed=ue)

    # Ping Command
    @commands.command(brief="Gets the bot's ping.")
    async def ping(self, ctx):
        ping_embed = discord.Embed(title="🏓 Pong!")
        ping_embed.add_field(
            name="Websocket Latency",
            value=f"`{round(self.avimetry.latency * 1000)}ms`",
            inline=False,
        )
        ping_embed.add_field(
            name="API Latency",
            value=f"`{await self.avimetry.api_latency(ctx)}ms`",
            inline=False,
        )
        ping_embed.add_field(
            name="Database Latency",
            value=f"`{await self.avimetry.database_latency(ctx)}ms`",
            inline=False,
        )
        await ctx.send(embed=ping_embed)

    # Source Command
    # Follow the license, Thanks. If you do use this code, you have to make your bot's source public.
    @commands.command(brief="Sends the bot's source")
    async def source(self, ctx):
        source_embed = discord.Embed(
            title=f"{self.avimetry.user.name}'s source code",
            timestamp=datetime.datetime.utcnow(),
        )
        if self.avimetry.user.id != 756257170521063444:
            source_embed.description = "This bot is made by [avi](https://discord.com/users/750135653638865017). \
                It is run off of this [source code](https://github.com/jbkn/avimetry).\nKeep the license in mind"
        else:
            source_embed.description = (
                "Here is my [source code](https://github.com/jbkn/avimetry) made by "
                "[avi](https://discord.com/users/750135653638865017).\nMake sure you follow the license."
            )
        await ctx.send(embed=source_embed)

    # Invite Command
    @commands.group(invoke_without_command=True)
    async def invite(self, ctx):
        invite_embed = discord.Embed(
            title=f"{self.avimetry.user.name} Invite",
            description=(
                "Invite me to your server! Here is the invite link.\n"
                f"[Here]({str(discord.utils.oauth_url(self.avimetry.user.id, discord.Permissions(2147483647)))}) "
                "is the invite link."
            ),
        )
        invite_embed.set_thumbnail(url=self.avimetry.user.avatar_url)
        await ctx.send(embed=invite_embed)

    @invite.command()
    async def bot(self, ctx, bot: discord.Member):
        bot_invite = discord.Embed()
        bot_invite.set_thumbnail(url=bot.avatar_url)
        if bot.bot:
            bot_invite.title = f"{bot.name} Invite"
            bot_invite.description = (
                f"Invite {bot.name} to your server! Here is the invite link.\n"
                f"Click [here]({str(discord.utils.oauth_url(bot.id, discord.Permissions(2147483647)))}) for the invite!"
            )
        else:
            bot_invite.title = f"{bot.name} Invite"
            bot_invite.description = "That is not a bot. Make sure you mention a bot."
        await ctx.send(embed=bot_invite)

    @commands.command(brief="Request a feature to be added to the bot.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def request(self, ctx, *, request):
        request_channel = self.avimetry.get_channel(817093957322407956)
        req_send = discord.Embed(
            title=f"Request from {str(ctx.author)}",
            description=f"```{request}```"
        )
        await request_channel.send(embed=req_send)
        req_embed = discord.Embed(
            title="Request sent",
            description=(
                "Thank you for your request! Join the [support] server to see if your request has been approved.\n"
                "Please note that spam requests will get you permanently blacklisted from this bot."
            )
        )
        req_embed.add_field(
            name="Your \"useful\" request",
            value=f"```{request}```"
        )
        await ctx.send(embed=req_embed)


def setup(avimetry):
    avimetry.add_cog(BotInfo((avimetry)))
