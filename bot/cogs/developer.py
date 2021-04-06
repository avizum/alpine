import typing
from utils.converters import CogConverter
import discord
import os
import datetime
from discord.ext import commands
from utils.context import AvimetryContext
import subprocess
import asyncio


class Owner(commands.Cog):
    '''
    Commands for bot owner.
    '''
    def __init__(self, avi):
        self.avi = avi

    def cog_unload(self):
        self.avi.load_extension("cogs.owner")

    async def cog_check(self, ctx: AvimetryContext):
        if await self.avi.is_owner(ctx.author) is True:
            return True
        raise commands.NotOwner("You do not own this bot.")

    @commands.group(
        invoke_without_command=True,
        hidden=True
    )
    async def dev(self, ctx: AvimetryContext):
        await ctx.send_help("dev")

    # Load Command
    @dev.command(brief="Load module")
    async def load(self, ctx: AvimetryContext, module: CogConverter):
        for cog in module:
            try:
                self.avi.reload_extension(cog)
            except Exception as e:
                print(e)

    # Unload Command
    @dev.command(brief="Unload module")
    async def unload(self, ctx: AvimetryContext, module: CogConverter):
        for cog in module:
            try:
                self.avi.reload_extension(cog)
            except Exception as e:
                print(e)

    # Reload Command
    @dev.command(
        brief="Reloads a module if it is not working.", usage="[extension]"
    )
    async def reload(self, ctx: AvimetryContext, module: CogConverter):
        reload_list = []
        for cog in module:
            try:
                self.avi.reload_extension(cog)
                reload_list.append(f'{self.avi.emoji_dictionary["green_tick"]} | {cog}')
            except Exception as e:
                reload_list.append(f'{self.avi.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        embed = discord.Embed(description="\n".join(reload_list))
        await ctx.send(embed=embed)

    @dev.command()
    async def prefixless(self, ctx: AvimetryContext, toggle: bool):
        await ctx.message.add_reaction(self.avi.emoji_dictionary["green_tick"])
        self.avi.devmode = toggle

    @dev.command(brief="Pulls from GitHub and then reloads all modules")
    async def sync(self, ctx: AvimetryContext):
        sync_embed = discord.Embed(
            title="Syncing with GitHub", description="Please Wait..."
        )
        edit_sync = await ctx.send(embed=sync_embed)
        await asyncio.sleep(2)
        output = []
        output.append(f'```{subprocess.getoutput("git pull")}```')
        sync_embed.description = "\n".join(output)
        sync_embed.timestamp = datetime.datetime.utcnow()
        sync_embed.title = "Synced With GitHub"
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    self.avi.reload_extension(f"cogs.{filename[:-3]}")
                except Exception as e:
                    sync_embed.add_field(
                        name=f"<:noTick:777096756865269760> {filename}",
                        value=e
                    )
        await edit_sync.edit(embed=sync_embed)

    # Reboot Command
    @dev.command(brief="Reboot the bot")
    async def reboot(self, ctx: AvimetryContext):
        sm = discord.Embed(
            description="Are you sure you want to reboot?"
        )
        rr = await ctx.confirm(embed=sm)
        if rr:
            await self.avi.close()
        if not rr:
            await ctx.send("Reboot Aborted", delete_after=5)
        

    # Leave command
    @dev.command()
    async def leave(self, ctx: AvimetryContext):
        await ctx.send("Okay bye")
        await ctx.guild.leave()

    @dev.command()
    async def blacklist(self, ctx: AvimetryContext, user: typing.Union[discord.User, discord.Member], *, reason):
        await self.avi.pool.execute(
            "INSERT INTO blacklist_user VALUES ($1, $2)",
            user.id, reason)
        ctx.cache.blacklisted_users[user.id] = reason

        embed = discord.Embed(
            title="Blacklisted User",
            description=(
                f"Added {user} to the blacklist.\n"
                f"Reason: `{reason}`"
            )
        )
        await ctx.send(embed=embed)

    @dev.command()
    async def unblacklist(self, ctx: AvimetryContext, user: typing.Union[discord.User, discord.Member]):
        await self.avi.pool.execute(
            "DELETE FROM blacklist_user WHERE user_id = $1",
            user.id
        )
        ctx.cache.blacklisted_users.pop(user.id)
        await ctx.send(f"Unblacklisted {str(user)}")


def setup(avi):
    avi.add_cog(Owner(avi))
