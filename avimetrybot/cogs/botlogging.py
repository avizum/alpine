import discord
from discord.ext import commands
import random
import datetime


class BotLogs(commands.Cog, name="bot logs"):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    async def get_logs(self, arg):
        logcheck = await self.avimetry.logs.find(arg)
        return logcheck

    @commands.Cog.listener("on_message_delete")
    async def message_delete(self, message: discord.Message):
        if message.guild is None:
            return
        delete_log = await self.get_logs(message.guild.id)
        if delete_log is None:
            return
        try:
            if (delete_log["delete_log"]) == False:
                return
        except KeyError:
            return
        if message.author == self.avimetry.user:
            return
        embed = discord.Embed(
            title="Message_Delete", timestamp=datetime.datetime.utcnow()
        )
        if message.content:
            embed.add_field(name="Deleted content", value=f">>> {message.content}")
        if not message.content:
            embed.add_field(
                name="Deleted content",
                value="Due to Discord's API limitations, embeds and images can not be logged. Sorry.",
            )

        if message.guild.me.guild_permissions.view_audit_log is True:
            deleted_by = (await message.guild.audit_logs(limit=1).flatten())[0]
            if deleted_by.action == discord.AuditLogAction.message_delete:
                if deleted_by.target == message.author:
                    embed.set_footer(
                        text=f"Deleted by {deleted_by.user}",
                        icon_url=deleted_by.user.avatar_url,
                    )

            embed.add_field(
                name="Information",
                value=f"Message Author: {message.author.mention},\nDeleted from {message.channel.mention} in {message.guild.name}",
                inline=False,
            )
        get_channel = await self.avimetry.logs.find(message.guild.id)
        send_channel = get_channel["logging_channel"]
        channel = self.avimetry.get_channel(send_channel)
        await channel.send(embed=embed)

    @commands.Cog.listener("on_message_edit")
    async def message_edit(self, before, after):
        if before.guild is None and after.guild is None:
            return
        else:
            pass
        edit_log = await self.get_logs(before.guild.id)
        if edit_log is None:
            return
        try:
            if (edit_log["edit_log"]) == False:
                return
        except KeyError:
            return
        if before.author == self.avimetry.user:
            return
        if before.content == after.content:
            return
        if len(before.content) > 1024:
            bef_con = f"{str(before.content[:1017])}..."
        else:
            bef_con = before.content
        if len(after.content) > 1024:
            aft_con = f"{str(after.content[0:1017])}..."
        else:
            aft_con = after.content
        embed = discord.Embed(
            title="Message_Edit", timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Message Before", value=f">>> {bef_con}", inline=False)
        embed.add_field(name="Message After", value=f">>> {aft_con}", inline=False)
        embed.add_field(
            name="Information",
            value=f"Message Author: {before.author.mention}\nEdited in {before.channel.mention} in {before.guild.name}",
        )
        get_channel = await self.avimetry.logs.find(before.guild.id)
        send_channel = get_channel["logging_channel"]
        channel = self.avimetry.get_channel(send_channel)
        await channel.send(embed=embed)

    @commands.Cog.listener("on_command")
    async def on_command(self, ctx):
        print(f"{ctx.command.name} completion")
        self.avimetry.commands_ran += 1


def setup(avimetry):
    avimetry.add_cog(BotLogs(avimetry))
