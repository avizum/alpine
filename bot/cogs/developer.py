import typing
import discord
import datetime
import subprocess
import asyncio
from utils.converters import CogConverter
from discord.ext import commands
from utils.context import AvimetryContext


class Owner(commands.Cog):
    '''
    Commands for bot owner.
    '''
    def __init__(self, avi):
        self.avi = avi

    def cog_unload(self):
        self.avi.load_extension("cogs.developer")

    def cleanup_code(self, content):
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        return content.strip('` \n')

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
    @dev.command(
        brief="Load module", aliases=["l"]
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

    # Unload Command
    @dev.command(
        brief="Unload module", aliases=["u"]
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

    # Reload Command
    @dev.command(
        brief="Reloads a module if it is not working.", aliases=["r"]
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
        output = [f'```{subprocess.getoutput("git pull")}```']
        sync_embed.description = "\n".join(output)
        sync_embed.timestamp = datetime.datetime.utcnow()
        sync_embed.title = "Synced With GitHub"
        modules = CogConverter().convert(ctx, "~")
        reload_list = []
        for cog in modules:
            try:
                self.avi.reload_extension(cog)
                reload_list.append(f'{self.avi.emoji_dictionary["green_tick"]} | {cog}')
            except Exception as e:
                reload_list.append(f'{self.avi.emoji_dictionary["red_tick"]} | {cog}```{e}```')
        sync_embed.add_field(name="Reloaded Modules", value="\n".join(reload_list))
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

    @dev.command()
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

    @dev.command(name="dev")
    async def _dev(self, ctx):
        await ctx.send("asd")


def setup(avi):
    avi.add_cog(Owner(avi))
