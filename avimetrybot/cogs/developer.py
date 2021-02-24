import discord
import os
import datetime
from discord.ext import commands
import subprocess
import asyncio


class Owner(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    def cog_unload(self):
        self.avimetry.load_extension("cogs.owner")

    # Load Command
    @commands.command(brief="Loads a module if it was disabled.")
    @commands.is_owner()
    async def load(self, ctx, extension=None):
        if extension is None:
            embed = discord.Embed(
                title="Load Modules", timestamp=datetime.datetime.utcnow()
            )
            for filename in os.listdir("./avimetrybot/cogs"):
                if filename.endswith(".py"):
                    try:
                        self.avimetry.load_extension(f"cogs.{filename[:-3]}")
                    except Exception as e:
                        embed.add_field(
                            name=f"<:noTick:777096756865269760> {filename}",
                            value=f"Load was not successful: {e}",
                            inline=True,
                        )
            await ctx.send(embed=embed)
            return
        try:
            self.avimetry.load_extension(f"cogs.{extension}")
            loadsuc = discord.Embed()
            loadsuc.add_field(
                name="<:yesTick:777096731438874634> Module Enabled",
                value=f"The **{extension}** module has been enabled.",
                inline=False,
            )
            await ctx.send(embed=loadsuc)
        except Exception as load_error:
            noload = discord.Embed()
            noload.add_field(
                name="<:noTick:777096756865269760> Module was not loaded",
                value=load_error,
                inline=False,
            )
            await ctx.send(embed=noload)

    # Unload Command
    @commands.command(brief="Unloads a module if it is being abused.")
    @commands.is_owner()
    async def unload(self, ctx, extension=None):
        if extension is None:
            embed = discord.Embed(
                title="Unload Modules", timestamp=datetime.datetime.utcnow()
            )
            for filename in os.listdir("./avimetrybot/cogs"):
                if filename.endswith(".py"):
                    try:
                        self.avimetry.unload_extension(f"cogs.{filename[:-3]}")
                    except Exception as e:
                        embed.add_field(
                            name=f"<:noTick:777096756865269760> {filename}",
                            value=f"Unload was not successful: {e}",
                            inline=True,
                        )
            await ctx.send(embed=embed)
            return
        try:
            self.avimetry.unload_extension(f"cogs.{extension}")
            unloadsuc = discord.Embed()
            unloadsuc.add_field(
                name="<:yesTick:777096731438874634> Module Disabled",
                value=f"The **{extension}** module has been disabled.",
                inline=False,
            )
            await ctx.send(embed=unloadsuc)
        except Exception as unload_error:
            unloudno = discord.Embed()
            unloudno.add_field(
                name="<:noTick:777096756865269760> Module not unloaded",
                value=unload_error,
            )
            await ctx.send(embed=unloudno)

    # Reload Command
    @commands.command(
        brief="Reloads a module if it is not working.", usage="[extension]"
    )
    @commands.is_owner()
    async def reload(self, ctx, module):
        if module == "~":
            embed = discord.Embed(
                title="Reload Modules",
                description="Reloaded all modules sucessfully.",
                timestamp=datetime.datetime.utcnow(),
            )
            for filename in os.listdir("./avimetrybot/cogs"):
                if filename.endswith(".py"):
                    try:
                        self.avimetry.reload_extension(f"cogs.{filename[:-3]}")
                    except Exception as e:
                        embed.description = "Reloaded all Modules sucessfully except the one(s) listed below:"
                        embed.add_field(
                            name=f"<:noTick:777096756865269760> {filename}",
                            value=f"Reload was not successful: {e}",
                            inline=True,
                        )
            return await ctx.send(embed=embed)
        try:
            self.avimetry.reload_extension(f"cogs.{module}")
            reload_finish = discord.Embed()
            reload_finish.add_field(
                name="<:yesTick:777096731438874634> Module Reloaded",
                value=f"The **{module}** module has been reloaded.",
                inline=False,
            )
            await ctx.send(embed=reload_finish)
        except Exception as reload_error:
            reload_fail = discord.Embed()
            reload_fail.add_field(
                name="<:noTick:777096756865269760> Module not reloaded",
                value=reload_error,
            )
            await ctx.send(embed=reload_fail)

    @commands.command()
    @commands.is_owner()
    async def devmode(self, ctx, toggle: bool):
        await ctx.send(f"dev mode is now {toggle}")
        self.avimetry.devmode = toggle

    @commands.command(brief="Pulls from GitHub and then reloads all modules")
    @commands.is_owner()
    async def sync(self, ctx):
        sync_embed = discord.Embed(
            title="Syncing with GitHub", description="Please Wait..."
        )
        edit_sync = await ctx.send_raw(embed=sync_embed)
        await asyncio.sleep(2)
        output = []
        output.append(f'```{subprocess.getoutput("git pull")}```')
        sync_embed.description = "\n".join(output)
        sync_embed.timestamp = datetime.datetime.utcnow()
        sync_embed.title = "Synced With GitHub"
        mod_list = []
        for filename in os.listdir("./avimetrybot/cogs"):
            if filename.endswith(".py"):
                try:
                    self.avimetry.reload_extension(f"cogs.{filename[:-3]}")
                except Exception as e:
                    mod_list.append(f"**{filename}**\n{e}")
        error_value = "\n".join(mod_list)
        if mod_list is None:
            error_value = "\u200b"
        sync_embed.add_field(name="Reloaded all modules except the ones listed below.", value=error_value)
        await edit_sync.edit(embed=sync_embed)

    # Shutdown Command
    @commands.command(brief="Reboot the bot")
    @commands.is_owner()
    async def reboot(self, ctx):
        sm = discord.Embed()
        sm.add_field(
            name=f"{self.avimetry.user.name} reboot",
            value="Are you sure you want to reboot?"
        )
        rr = await ctx.send(embed=sm)
        reactions = ["<:yesTick:777096731438874634>", "<:noTick:777096756865269760>"]
        for reaction in reactions:
            await rr.add_reaction(reaction)

        def check(reaction, user):
            return (
                str(reaction.emoji) in ["<:yesTick:777096731438874634>", "<:noTick:777096756865269760>"] and user != self.avimetry.user and user == ctx.author
            )

        try:
            # pylint: disable=unused-variable
            reaction, user = await self.avimetry.wait_for(
                "reaction_add", check=check, timeout=60
            )
        except asyncio.TimeoutError:
            to = discord.Embed()
            to.add_field(name=f"{self.avimetry.user.name} rebooting", value="Timed Out.")
            await rr.edit(embed=to)
            await rr.clear_reactions()
        else:
            if str(reaction.emoji) == "<:yesTick:777096731438874634>":
                rre = discord.Embed()
                rre.add_field(
                    name=f"{self.avimetry.user.name} rebooting", value="rebooting..."
                )
                await rr.edit(embed=rre)
                await rr.clear_reactions()
                await asyncio.sleep(5)
                await rr.delete()
                await self.avimetry.close()
            if str(reaction.emoji) == "<:noTick:777096756865269760>":
                rre2 = discord.Embed()
                rre2.add_field(
                    name=f"{self.avimetry.user.name} rebooting",
                    value="reboot has been cancelled.",
                )
                await rr.edit(embed=rre2)
                await rr.clear_reactions()
                await asyncio.sleep(5)
                await rr.delete()
            # pylint: enable=unused-variable

    # Leave command
    @commands.command()
    @commands.is_owner()
    async def leave(self, ctx):
        await ctx.send("Okay bye")
        await ctx.guild.leave()

    @commands.command()
    @commands.is_owner()
    async def dev(self, ctx, command, *args):
        exec = self.avimetry.get_command(command)
        await exec(ctx, *args)


def setup(avimetry):
    avimetry.add_cog(Owner(avimetry))
