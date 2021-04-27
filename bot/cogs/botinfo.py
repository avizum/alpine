import discord
import datetime
import psutil
import humanize
from discord.ext import commands
from utils.context import AvimetryContext


class BotInfo(commands.Cog, name="Bot Info"):
    """
    Commands for the bot's information.
    """
    def __init__(self, avi):
        self.avi = avi

    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.avi.get_context(message, cls=AvimetryContext)
        if message.author == self.avi.user:
            return
        if message.content == f"<@!{self.avi.user.id}>":
            prefix = self.avi.get_command("prefix")
            await prefix(ctx)

    @commands.command()
    async def about(self, ctx: AvimetryContext):
        embed = discord.Embed(title="Info about Avimetry")
        embed.add_field(
            name="Latest Updates",
            value="New Database! Migrating will take a bit, So prefixes, configuration may be broken."
        )
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
        embed.add_field(name="Commands", value=f"{len(self.avi.commands)} usable")
        embed.add_field(name="Commands ran", value=self.avi.commands_ran)
        embed.set_thumbnail(url=ctx.me.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(brief="Get the bot's uptime")
    async def uptime(self, ctx: AvimetryContext):
        delta_uptime = datetime.datetime.utcnow() - self.avi.launch_time
        ue = discord.Embed(
            title="Current Uptime",
            description=humanize.precisedelta(delta_uptime, format="%.2g"),
        )
        await ctx.send(embed=ue)

    @commands.command(brief="Gets the bot's ping.")
    async def ping(self, ctx: AvimetryContext):
        ping_embed = discord.Embed(title="🏓 Pong!")
        ping_embed.add_field(
            name="Websocket Latency",
            value=f"`{round(self.avi.latency * 1000)}ms`",
            inline=False)
        ping_embed.add_field(
            name="API Latency",
            value=f"`{await self.avi.api_latency(ctx)}ms`",
            inline=False)
        ping_embed.add_field(
            name="Database Latency (Mongo)",
            value=f"`{await self.avi.database_latency(ctx)}ms`",
            inline=False)
        ping_embed.add_field(
            name="Database Latency (PostgreSQL)",
            value=f"`{await self.avi.postgresql_latency()}ms`",
            inline=False)

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
                "Thank you for your request! Join the [support](https://discord.gg/NM7E7Rxy) server to see if \n"
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
