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
        rr = await ctx.confirm(embed=sm)
        if rr:
            await self.avi.close()
        if not rr:
            await ctx.send("Reboot Aborted", delete_after=5)

    @dev.command()
    async def leave(self, ctx: AvimetryContext):
        await ctx.send("Okay bye")
        await ctx.guild.leave()

    @dev.command()
    async def blacklist(self, ctx: AvimetryContext, user: typing.Union[discord.User, discord.Member], *, reason):
        try:
            ctx.cache.blacklist[user.id]
            return await ctx.send(f"{user} is already blacklisted.")
        except Exception:
            query = "INSERT INTO user_settings VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET blacklist = $2"
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
                    f"You were __**blacklisted**__ from using this bot by `{ctx.author}`.\n"
                    f"Reason: `{reason}`\n"
                    f"You can appeal at the Support Server."
                ),
                timestamp=datetime.datetime.utcnow(),
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass
        await ctx.send(embed=embed)

    @dev.command()
    async def unblacklist(self, ctx: AvimetryContext, user: typing.Union[discord.User, discord.Member], *, reason):
        try:
            ctx.cache.blacklist[user.id]
        except Exception:
            return await ctx.send(f"{user} is not blacklisted")
        query = "UPDATE user_settings SET blacklist = $1 WHERE user_id = $2"
        await self.avi.pool.execute(query, None, user.id)
        del ctx.cache.blacklist[user.id]
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


def setup(avi):
    avi.add_cog(Owner(avi))
