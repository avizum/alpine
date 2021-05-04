import logging
import discord
import datetime
from config import webhooks
from discord.ext import commands
from utils import AvimetryContext


logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


class Setup(commands.Cog):
    def __init__(self, avi):
        self.avi = avi
        self.guild_webhook = discord.Webhook.from_url(
            webhooks["join_log"],
            adapter=discord.AsyncWebhookAdapter(self.avi.session)
        )
        self.command_webhook = discord.Webhook.from_url(
            webhooks["command_log"],
            adapter=discord.AsyncWebhookAdapter(self.avi.session)
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.avi.cache.cache_new_guild(guild.id)
        await self.avi.cache.check_for_cache()
        message = [
            f"I got added to a server named {guild.name} with a total of {guild.member_count} members.",
            f"I am now in {len(self.avi.guilds)} guilds."
        ]
        members = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        if bots > members:
            message.append(f"There are more bots than members ({members}M, {bots}B), so it may be a bot farm.")
        await self.guild_webhook.send("\n".join(message), username="Joined Guild")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.avi.cache.delete_all(guild.id)
        message = [
            f"I got removed from a server named {guild.name}.",
            f"I am now in {len(self.avi.guilds)} guilds."
        ]
        await self.guild_webhook.send("\n".join(message), username="Left Guild")

    @commands.Cog.listener("on_command")
    async def on_command(self, ctx: AvimetryContext):
        embed = discord.Embed(
            title=f"Command: {ctx.command.name}",
            description=f"Command was ran in {ctx.guild.name} by {ctx.author.mention}"
        )
        embed.timestamp = datetime.datetime.utcnow()
        await self.command_webhook.send(embed=embed)
        self.avi.commands_ran += 1


def setup(avi):
    avi.add_cog(Setup(avi))
