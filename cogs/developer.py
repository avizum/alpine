"""
Commands for me and other owners
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

import typing
import discord
import datetime
import subprocess
import asyncio

from discord.ext import commands
from jishaku.codeblocks import codeblock_converter
from utils import AvimetryBot, AvimetryContext, CogConverter


class Owner(commands.Cog, command_attrs={"hidden": True}):
    """
    Commands for the bot owners.
    """
    def __init__(self, avi):
        self.avi: AvimetryBot = avi

    def cog_unload(self):
        self.avi.load_extension("cogs.developer")

    def cleanup_code(self, content):
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        return content.strip('` \n')

    async def cog_check(self, ctx: AvimetryContext):
        if await self.avi.is_owner(ctx.author) is True:
            return True
        raise commands.NotOwner("Stay away.")

    @commands.group(
        invoke_without_command=True,
        brief="Developer commands only."
    )
    async def dev(self, ctx: AvimetryContext):
        await ctx.send_help("dev")

    @dev.command(
        brief="Load module(s)", aliases=["l"]
        )
    async def load(self, ctx: AvimetryContext, module: CogConverter):
        reload_list = []
        for cog in module:
            try:
                self.avi.load_extension(cog)
                reload_list.append(f'{self.avi.emoji_dictionary["green_tick"]} | {cog}')
            except Exception as e:
                reload_list.append(f'{self.avi.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        embed = discord.Embed(title="Load", description="\n".join(reload_list))
        await ctx.send(embed=embed)

    @dev.command(
        brief="Unload module(s)", aliases=["u"]
        )
    async def unload(self, ctx: AvimetryContext, module: CogConverter):
        unload_list = []
        for cog in module:
            try:
                self.avi.unload_extension(cog)
                unload_list.append(f'{self.avi.emoji_dictionary["green_tick"]} | {cog}')
            except Exception as e:
                unload_list.append(f'{self.avi.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        embed = discord.Embed(title="Unload", description="\n".join(unload_list))
        await ctx.send(embed=embed)

    @dev.command(
        brief="Reload module(s)", aliases=["r"]
    )
    async def reload(self, ctx: AvimetryContext, module: CogConverter):
        reload_list = []
        for cog in module:
            try:
                self.avi.reload_extension(cog)
                reload_list.append(f'{self.avi.emoji_dictionary["green_tick"]} | {cog}')
            except Exception as e:
                reload_list.append(f'{self.avi.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        embed = discord.Embed(title="Reload", description="\n".join(reload_list))
        await ctx.send(embed=embed)

    @dev.command(brief="Pulls from GitHub and then reloads all modules")
    async def sync(self, ctx: AvimetryContext):
        sync_embed = discord.Embed(
            title="Syncing with GitHub", description="Please Wait..."
        )
        edit_sync = await ctx.send(embed=sync_embed)
        await asyncio.sleep(2)
        output = [f'```{subprocess.getoutput("git pull")}```']
        sync_embed.description = "\n".join(output)
        sync_embed.timestamp = datetime.datetime.utcnow()
        sync_embed.title = "Synced With GitHub"
        modules = await CogConverter().convert(ctx, "~")
        reload_list = []
        for cog in modules:
            try:
                self.avi.reload_extension(cog)
                reload_list.append(f'{self.avi.emoji_dictionary["green_tick"]} | {cog}')
            except Exception as e:
                reload_list.append(f'{self.avi.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        sync_embed.add_field(name="Reloaded Modules", value="\n".join(reload_list))
        await edit_sync.edit(embed=sync_embed)

    @dev.command(brief="Reboot the bot")
    async def reboot(self, ctx: AvimetryContext):
        sm = discord.Embed(
            description="Are you sure you want to reboot?"
        )
        conf = await ctx.confirm(embed=sm)
        if conf:
            await self.avi.close()
        if not conf:
            await ctx.send("Reboot Aborted", delete_after=5)

    @dev.command(brief="Jishaku alias")
    async def eval(self, ctx: AvimetryContext, *, code: codeblock_converter):
        jsk = self.avi.get_command("jsk py")
        await jsk(ctx, argument=code)

    @dev.command(brief="Leaves a server.")
    async def leave(self, ctx: AvimetryContext, guild: discord.Guild):
        conf = await ctx.confirm(f"Are you sure you want me to leave {guild.name} ({guild.id})?")
        if conf:
            await ctx.guild.leave()
            return await ctx.message.add_reaction(self.avi.emoji_dictionary["green_tick"])
        await ctx.send("Okay, Aborted.")

    @dev.group(
        invoke_without_command=True,
        brief="Blacklist users from the bot",
        aliases=["bl"]
    )
    async def blacklist(self, ctx: AvimetryContext):
        bl_users = ctx.cache.blacklist.keys()
        joiner = "\n"
        embed = discord.Embed(
            title=f"List of blacklisted users ({len(bl_users)})",
            description=f"```\n{joiner.join([str(bl) for bl in bl_users])}```"
        )
        await ctx.send(embed=embed)

    @blacklist.command(
        name="add",
        aliases=["a"],
        brief="Adds a user to the global blacklist"
    )
    async def blacklist_add(self, ctx: AvimetryContext, user: typing.Union[discord.User, discord.Member], *, reason):
        try:
            ctx.cache.blacklist[user.id]
            return await ctx.send(f"{user} is already blacklisted.")
        except Exception:
            query = "INSERT INTO blacklist  VALUES ($1, $2)"
            await self.avi.pool.execute(query, user.id, reason)
            ctx.cache.blacklist[user.id] = reason

        embed = discord.Embed(
            title="Blacklisted User",
            description=(
                f"Added {user} to the blacklist.\n"
                f"Reason: `{reason}`"
            )
        )
        try:
            dm_embed = discord.Embed(
                title="Bot Moderator Action: Blacklist",
                description=(
                    f"You have been __**blacklisted**__ from this bot by `{ctx.author}`.\n"
                    f"Reason: `{reason}`\n"
                    f"You can appeal at the Support Server."
                ),
                timestamp=datetime.datetime.utcnow(),
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        await ctx.send(embed=embed)

    @blacklist.command(
        name="remove",
        aliases=["r"],
        brief="Remove a user from the blacklist."
    )
    async def blacklist_remove(self, ctx: AvimetryContext, user: typing.Union[discord.User, discord.Member], *, reason):
        try:
            ctx.cache.blacklist[user.id]
        except Exception:
            return await ctx.send(f"{user} is not blacklisted")
        query = "DELETE FROM blacklist WHERE user_id=$1"
        await self.avi.pool.execute(query, user.id)
        self.avi.cache.blacklist.pop(user.id)
        try:
            dm_embed = discord.Embed(
                title="Bot Moderator Action: Unblacklist",
                description=(
                    f"You have __**unblacklisted**__ from using this bot by `{ctx.author}`.\n"
                    f"Reason: `{reason}`\n"
                    f"You can get blacklisted again at the Support Server."
                ),
                timestamp=datetime.datetime.utcnow(),
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        await ctx.send(f"Unblacklisted {str(user)}")

    @dev.command(
        brief="Cleans up bot messages only"
    )
    async def cleanup(self, ctx: AvimetryContext, amount: int = 15):
        deleted = 0
        async for message in ctx.channel.history(limit=amount*2):
            if message.author.id == ctx.bot.user.id:
                try:
                    await message.delete()
                except Exception:
                    pass
                deleted += 1
                if deleted >= amount:
                    break
        await ctx.send(f"Successfully purged `{deleted}` message(s).")

    @dev.command()
    async def errors(self, ctx: AvimetryContext):
        raise Exception


def setup(avi):
    avi.add_cog(Owner(avi))
