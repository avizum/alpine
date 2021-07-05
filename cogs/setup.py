"""
Cog for Avimetry's setup with servers.
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
import datetime

from discord.ext import commands
from utils import AvimetryContext, AvimetryBot


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot: AvimetryBot = bot
        self.webhooks = self.bot.settings["webhooks"]
        self.guild_webhook = discord.Webhook.from_url(
            self.webhooks["join_log"],
            adapter=discord.AsyncWebhookAdapter(self.bot.session)
        )
        self.command_webhook = discord.Webhook.from_url(
            self.webhooks["command_log"],
            adapter=discord.AsyncWebhookAdapter(self.bot.session)
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if self.bot.user.id != 756257170521063444:
            return
        await self.bot.cache.cache_new_guild(guild.id)
        await self.bot.cache.check_for_cache()
        message = [
            f"I got added to a server named {guild.name} ({guild.id}) with a total of {guild.member_count} members.",
            f"I am now in {len(self.bot.guilds)} guilds."
        ]
        members = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        if bots > members:
            message.append(f"There are {bots} bots and {members} members so it may be a bot farm.")
        await self.guild_webhook.send("\n".join(message), username="Joined Guild")
        if not guild.chunked:
            await guild.chunk()
        channel = discord.utils.get(guild.text_channels, name='general')
        if not channel:
            channel = guild.text_channels[0]
        try:
            await channel.send('Thank you for adding me to your server! To get started use `a.help`')
        except discord.Forbidden:
            return

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if self.bot.user.id != 756257170521063444:
            return
        await self.bot.cache.delete_all(guild.id)
        message = [
            f"I got removed from a server named {guild.name}.",
            f"I am now in {len(self.bot.guilds)} guilds."
        ]
        await self.guild_webhook.send("\n".join(message), username="Left Guild")

    @commands.Cog.listener("on_command")
    async def on_command(self, ctx: AvimetryContext):
        try:
            self.bot.command_usage[ctx.command] += 1
        except KeyError:
            self.bot.command_usage[ctx.command] = 1
        if ctx.author.id in ctx.cache.blacklist or self.bot.user.id != 756257170521063444:
            return
        embed = discord.Embed(
            description=(
                f"Command: {ctx.command.qualified_name}\n"
                f"Message: {ctx.message.content}\n"
                f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
                f"Channel: {ctx.channel} ({ctx.channel.id})\n"
            ),
            color=ctx.author.color
        )
        embed.set_author(name=ctx.author, icon_url=str(ctx.author.avatar_url_as(format="png", size=512)))
        embed.timestamp = datetime.datetime.utcnow()
        await self.command_webhook.send(embed=embed)
        if ctx.guild.chunked:
            await ctx.guild.chunk()
        self.bot.commands_ran += 1


def setup(bot):
    bot.add_cog(Setup(bot))
