import discord
import datetime
from discord.ext import commands, tasks
from utils.context import AvimetryContext


class BotLogs(commands.Cog):
    def __init__(self, avi):
        self.avi = avi
        self.clear_cache.start()

    async def get_logs(self, arg):
        logcheck = await self.avi.logs.find(arg)
        return logcheck

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete(self, message: discord.Message):
        if not message.guild:
            return
        thing = self.avi.temp.logging_cache.get(message.guild.id)
        if not thing:
            return
        elif thing["enabled"] is not True:
            return
        elif thing["message_delete"] is False:
            return
        elif message.author == self.avi.user or message.author.bot:
            return
        embed = discord.Embed(
            title="Message Delete", timestamp=datetime.datetime.utcnow(),
            description=f"Message was deleted by {message.author.mention} in {message.channel.mention}"
        )
        embed.set_footer(text="Deleted at")
        if message.content:
            embed.add_field(name="Deleted content", value=f">>> {message.content}")
        if not message.content:
            return
        if message.guild.me.guild_permissions.view_audit_log is True:
            deleted_by = (await message.guild.audit_logs(limit=1).flatten())[0]
            if (
                deleted_by.action == discord.AuditLogAction.message_delete
                and deleted_by.target == message.author
            ):
                embed.set_footer(
                    text=f"Deleted by {deleted_by.user}",
                    icon_url=deleted_by.user.avatar_url,
                )
        channel_id = thing["channel_id"]
        channel = discord.utils.get(message.guild.channels, id=channel_id)
        await channel.send(embed=embed)

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.guild is None and after.guild is None:
            return
        thing = self.avi.temp.logging_cache.get(before.guild.id)
        if not thing:
            return
        elif thing["enabled"] is not True:
            return
        elif thing["message_edit"] is False:
            return
        elif before.author == self.avi.user or before.author.bot:
            return
        elif before.content == after.content:
            return
        bef_con = f"{str(before.content[:1017])}..." if len(before.content) > 1024 else before.content
        aft_con = f"{str(after.content[:1017])}..." if len(after.content) > 1024 else after.content
        embed = discord.Embed(
            title="Message Edit", timestamp=datetime.datetime.utcnow(),
            description=f"Message was edited by {before.author.mention} in {before.channel.mention}"
        )
        embed.add_field(name="Message Before", value=f">>> {bef_con}", inline=False)
        embed.add_field(name="Message After", value=f">>> {aft_con}", inline=False)
        embed.set_footer(text="Edited at")
        channel_id = thing["channel_id"]
        channel = discord.utils.get(before.guild.channels, id=channel_id)
        await channel.send(embed=embed)

    @commands.Cog.listener("on_command")
    async def on_command(self, ctx: AvimetryContext):
        self.avi.commands_ran += 1

    @tasks.loop(minutes=30)
    async def clear_cache(self):
        self.avi.command_cache.clear()

    @clear_cache.before_loop
    async def before_clear_cahce(self):
        await self.avi.wait_until_ready()


def setup(avi):
    avi.add_cog(BotLogs(avi))
