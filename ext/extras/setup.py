"""
Cog for Avimetry's setup with servers.
Copyright (C) 2021 - present avizum

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

import aiohttp
import discord
import datetime
import core

from discord.ext import commands
from utils import AvimetryContext, AvimetryBot


class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message):
        return (message.channel.id, message.content)


class Setup(core.Cog):
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now(datetime.timezone.utc)
        self.content_cd = CooldownByContent.from_cooldown(5.0, 20.0, commands.BucketType.user)
        self.user_cd = commands.CooldownMapping.from_cooldown(10.0, 40, commands.BucketType.user)
        self.webhooks = self.bot.settings["webhooks"]
        self.guild_webhook = discord.Webhook.from_url(
            self.webhooks["join_log"],
            session=self.bot.session
        )
        self.command_webhook = discord.Webhook.from_url(
            self.webhooks["command_log"],
            session=self.bot.session
        )
        self.command_webhook2 = discord.Webhook.from_url(
            self.webhooks["command_log2"],
            session=self.bot.session
        )
        self.request_wh = discord.Webhook.from_url(
            self.webhooks["request_log"],
            session=self.bot.session
        )

    @core.Cog.listener()
    async def on_message(self, message: discord.Message):
        ctx = await self.bot.get_context(message)
        if await self.bot.is_owner(ctx.author) and ctx.valid:
            return
        if message.author.bot:
            return
        if isinstance(message.channel, discord.DMChannel):
            cache = self.bot.cache.users.get(message.author.id)
            if cache:
                dmed = cache.get('dmed')
                if not dmed:
                    await message.channel.send('Hey, these DMs are logged and sent to the support server.')
                    cache['dmed'] = True
            embed = discord.Embed(title=f"DM from {message.author}", description=message.content)
            embed.set_footer(text=message.author.id)
            ts = message.created_at.timestamp()
            content_bucket = self.content_cd.get_bucket(message)
            user_bucket = self.user_cd.get_bucket(message)
            if content_bucket.update_rate_limit(ts) or user_bucket.update_rate_limit(ts):
                return
            await self.request_wh.send(embed=embed)
        try:
            if message.channel.id == 817093957322407956:
                resolved = message.reference.resolved.embeds[0]
                if resolved.footer.text.isdigit():
                    user = self.bot.get_user(int(resolved.footer.text))
                    if user:
                        send_embed = discord.Embed(
                            title=f"Message from {message.author}",
                            description=f"> {resolved.description}\n{message.content}"
                        )
                        await user.send(embed=send_embed)
        except AttributeError:
            return

    @core.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if self.bot.user.id != 756257170521063444:
            return
        await self.bot.cache.cache_new_guild(guild.id)
        await self.bot.cache.check_for_cache()
        members = sum(not m.bot for m in guild.members)
        bots = sum(m.bot for m in guild.members)
        summary = [
            f"I was just added to a guild named {guild.name} ({guild.id}).",
            f"Guild owner is {guild.owner} ({guild.owner_id}).",
            f"There are {bots} bots and {members} members in this guild. "
        ]
        if bots > members:
            summary.append("This guild may be a bot farm.")
        summary.append(f"I am now in a total of {len(self.bot.guilds)} guilds.")
        embed = discord.Embed(title="New guild", description='\n'.join(summary), color=guild.owner.color)
        embed.set_thumbnail(url=guild.icon.url)
        await self.guild_webhook.send(embed=embed, username="Joined Guild")
        if not guild.chunked:
            await guild.chunk()
        embed = discord.Embed(
            title='\U0001f44b Hey, I am Avimetry!',
            description='Hello, thank you for adding me to your server. Here are some commands to get you started.',
            color=guild.owner.color
        )
        embed.add_field(name='a.help', value='Sends the help page.', inline=False)
        embed.add_field(
            name='a.prefix add',
            value='Adds a prefix to this server. (You can have up to 15 prefixes)',
            inline=False
        )
        embed.add_field(name='a.about', value='Show some info about the bot.', inline=False)
        embed.add_field(name='a.vote', value='You can support Avimetry by voting! Thank you!', inline=False)
        embed.set_footer(text='Made by avizum :)')
        channel = discord.utils.get(guild.text_channels, name='general')
        if not channel:
            channels = [channel for channel in guild.text_channels if channel.permissions_for(guild.me).send_messages]
            channel = channels[0]
        await channel.send(embed=embed)

    @core.Cog.listener()
    async def on_guild_remove(self, guild):
        if self.bot.user.id != 756257170521063444:
            return
        await self.bot.cache.delete_all(guild.id)

        message = [
            f"I got removed from a server named {guild.name} ({guild.id}).",
            f"Guild owner is {guild.owner}",
            f"I am now in a total of {len(self.bot.guilds)} guilds."
        ]
        embed = discord.Embed(title="Left Guild", description="\n".join(message))
        await self.guild_webhook.send(embed=embed, username="Left Guild")

    @core.Cog.listener("on_command")
    async def on_command(self, ctx: AvimetryContext):
        if not ctx.guild:
            return
        try:
            self.bot.command_usage[str(ctx.command)] += 1
        except KeyError:
            self.bot.command_usage[str(ctx.command)] = 1
        if ctx.author.id in ctx.cache.blacklist or self.bot.user.id != 756257170521063444:
            return
        embed = discord.Embed(color=await ctx.determine_color())
        embed.description = (
            f"Command: {ctx.command.qualified_name}\n"
            f"Message: {ctx.message.content}\n"
            f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
            f"Channel: {ctx.channel} ({ctx.channel.id})\n"
        )
        embed.set_author(name=ctx.author, icon_url=str(ctx.author.avatar.replace(format="png", size=512)))
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        try:
            if await self.bot.is_owner(ctx.author):
                await self.command_webhook.send(embed=embed)
            else:
                await self.command_webhook2.send(embed=embed)
        except aiohttp.ClientOSError:
            return
        if not ctx.guild.chunked:
            await ctx.guild.chunk()
        self.bot.commands_ran += 1


def setup(bot):
    bot.add_cog(Setup(bot))
