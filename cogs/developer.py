"""
Commands for developers
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
import asyncio
import utils

from utils import core
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter
from utils import AvimetryBot, AvimetryContext, CogConverter


class Owner(commands.Cog):
    """
    Commands for the bot developers.
    """
    def __init__(self, bot: AvimetryBot):
        self.bot = bot
        self.load_time = datetime.datetime.now()

    def cleanup_code(self, content):
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        return content.strip('` \n')

    async def cog_check(self, ctx: AvimetryContext):
        if await self.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner("Stay away.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        waste = "\U0001f5d1\U0000fe0f"
        if reaction.emoji == waste and await self.bot.is_owner(user) and reaction.message.author == self.bot.user:
            await reaction.message.delete()

    @core.group(
        invoke_without_command=True,
        brief="Developer commands only.",
        aliases=["dev"],
        user_permissions='Bot Owner',
        hidden=True
    )
    async def developer(self, ctx: AvimetryContext):
        await ctx.send_help("developer")

    @developer.command(
        brief="Load module(s)", aliases=["l"]
        )
    async def load(self, ctx: AvimetryContext, module: CogConverter):
        load_list = []
        for cog in module:
            try:
                self.bot.load_extension(cog)
                load_list.append(f'{self.bot.emoji_dictionary["green_tick"]} | {cog}')
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                load_list.append(f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        embed = discord.Embed(title="Loaded cogs", description="\n".join(load_list))
        await ctx.send(embed=embed, delete_after=15)

    @developer.command(
        brief="Unload module(s)", aliases=["u"]
        )
    async def unload(self, ctx: AvimetryContext, module: CogConverter):
        unload_list = []
        for cog in module:
            try:
                self.bot.unload_extension(cog)
                unload_list.append(f'{self.bot.emoji_dictionary["green_tick"]} | {cog}')
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                unload_list.append(f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        embed = discord.Embed(title="Unloaded cogs", description="\n".join(unload_list))
        await ctx.send(embed=embed, delete_after=15)

    @developer.command(
        brief="Reload module(s)", aliases=["r"]
    )
    async def reload(self, ctx: AvimetryContext, module: CogConverter):
        reload_list = []
        for cog in module:
            try:
                self.bot.reload_extension(cog)
                reload_list.append(f'{self.bot.emoji_dictionary["green_tick"]} | {cog}')
            except (commands.ExtensionError, ModuleNotFoundError) as e:
                reload_list.append(f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        description = "\n".join(reload_list)
        embed = discord.Embed(title="Reloaded cogs", description=description)
        await ctx.send(embed=embed, delete_after=15)

    @developer.command(brief="Pulls from GitHub and then reloads all modules")
    async def sync(self, ctx: AvimetryContext):
        sync_embed = discord.Embed(
            title="Syncing with GitHub", description="Please Wait..."
        )
        edit_sync = await ctx.send(embed=sync_embed)
        proc = await asyncio.create_subprocess_shell(
            'git pull',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await proc.communicate()

        if stdout:
            output = f'[stdout]\n{stdout.decode()}'
        elif stderr:
            output = f'[stderr]\n{stderr.decode()}'

        sync_embed.description = f"```bash\n{output}\n```"
        sync_embed.timestamp = datetime.datetime.utcnow()
        sync_embed.title = "Synced With GitHub"
        modules = await CogConverter().convert(ctx, "~")
        reload_list = []
        for cog in modules:
            try:
                self.bot.reload_extension(cog)
            except commands.ExtensionError as e:
                reload_list.append(f'{self.bot.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        if not reload_list:
            value = "All modules were reloaded successfully"
        else:
            value = "\n".join(reload_list)
        sync_embed.add_field(name="Reloaded Modules", value=value)
        await edit_sync.edit(embed=sync_embed, delete_after=15)

    @developer.command(brief="Reboot the bot", aliases=["shutdown"])
    async def reboot(self, ctx: AvimetryContext):
        sm = discord.Embed(
            description=f"Are you sure you want to {ctx.invoked_with}?"
        )
        conf = await ctx.confirm(embed=sm)
        if conf:
            await self.bot.close()
        if not conf:
            await ctx.send(f"{ctx.invoked_with.capitalize()} Aborted", delete_after=5)

    @developer.command(brief="Evaluate python code.")
    async def eval(self, ctx: AvimetryContext, *, code: codeblock_converter):
        jsk = self.bot.get_command("jsk py")
        if jsk:
            await jsk(ctx, argument=code)
        else:
            await ctx.send("Jishaku is not loaded.")

    @developer.command(brief="Leaves a server.")
    async def leave(self, ctx: AvimetryContext, guild: discord.Guild):
        conf = await ctx.confirm(f"Are you sure you want me to leave {guild.name} ({guild.id})?")
        if conf:
            await ctx.guild.leave()
            return await ctx.message.add_reaction(self.bot.emoji_dictionary["green_tick"])
        await ctx.send("Okay, Aborted.")

    @developer.group(
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
        except KeyError:
            query = "INSERT INTO blacklist VALUES ($1, $2)"
            await self.bot.pool.execute(query, user.id, reason)
            ctx.cache.blacklist[user.id] = reason

        embed = discord.Embed(
            title="Blacklisted User",
            description=(
                f"Added {user} to the blacklist.\n"
                f"Reason: `{reason}`"
            )
        )
        await ctx.send(embed=embed)

    @blacklist.command(
        name="remove",
        aliases=["r"],
        brief="Remove a user from the blacklist."
    )
    async def blacklist_remove(self, ctx: AvimetryContext, user: typing.Union[discord.User, discord.Member], *, reason):
        try:
            ctx.cache.blacklist[user.id]
        except KeyError:
            return await ctx.send(f"{user} is not blacklisted")
        query = "DELETE FROM blacklist WHERE user_id=$1"
        await self.bot.pool.execute(query, user.id)
        self.bot.cache.blacklist.pop(user.id)
        await ctx.send(f"Unblacklisted {str(user)}")

    @developer.command(
        brief="Cleans up bot messages only"
    )
    async def cleanup(self, ctx: AvimetryContext, amount: int = 15):
        def check(m: discord.Message):
            return m.author == self.bot.user
        perms = ctx.channel.permissions_for(ctx.me).manage_messages
        purged = await ctx.channel.purge(limit=amount, check=check, bulk=perms)
        await ctx.can_delete(f'Purged {len(purged)} messages')

    @developer.command()
    async def maintenance(self, ctx: AvimetryContext, toggle: bool):
        match = {
            True: "enabled",
            False: "disabled"
        }
        self.bot.maintenance = toggle
        await ctx.send(f"Maintenance mode has been {match[toggle]}")

    @developer.command()
    async def cogs(self, ctx: AvimetryContext, cog: str = None):
        thing_list = [
            f"{key.title()} | Loaded {utils.timestamp(val.load_time, 'R')}"
            for key, val in self.bot.cogs.items()
        ]
        embed = discord.Embed(title="Loaded Cogs", description='\n'.join(thing_list))
        await ctx.send(embed=embed)

    @developer.group(invoke_without_command=True, aliases=["error"])
    async def errors(self, ctx: AvimetryContext):
        errors = await self.bot.pool.fetch('SELECT * FROM command_errors WHERE fixed = false')
        embed = discord.Embed(title="Errors")
        for error in errors:
            embed.add_field(
                name=f"{error['command']} | `{error['id']}`",
                value=f"```py\n{error['error']}```", inline=False
            )
        if not errors:
            embed.add_field(name='No errors found', value='Nice :)')
        await ctx.send(embed=embed)

    @errors.command()
    async def fix(self, ctx: AvimetryContext, error_id: int):
        query = "SELECT * FROM command_errors WHERE id=$1"
        error_info = await self.bot.pool.fetchrow(query, error_id)
        if not error_info:
            return await ctx.send("This error does not exist.")
        elif error_info['fixed'] is True:
            return await ctx.send('This error is already marked as fixed.')
        query = "UPDATE command_errors SET fixed=$1 WHERE id=$2"
        await self.bot.pool.execute(query, True, error_id)
        await ctx.send(f"Error #{error_id} has been marked as fixed.")


def setup(bot):
    bot.add_cog(Owner(bot))
