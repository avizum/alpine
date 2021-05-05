import discord
import string
import random
import asyncio
import datetime
from discord.ext import commands
from utils.context import AvimetryContext


class MemberJoin(commands.Cog):
    def __init__(self, avi):
        self.avi = avi

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        prefixes = await self.avi.cache.get_guild_settings(member.guild.id)
        global pre
        pre = "a." if not prefixes["prefixes"] else prefixes["prefixes"][0]
        try:
            config = self.avi.cache["guild_id"]
        except KeyError:
            return
        if config["verify"] is not True:
            return

        name = "New Members"
        category = discord.utils.get(member.guild.categories, name=name)
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
        }
        await member.guild.create_text_channel(
            f"{member.name.lower().replace(' ', '-')}-verification",
            category=category,
            reason=f"Started Verification for {member.name}",
            overwrites=overwrites,
        )

        channel = discord.utils.get(
            member.guild.channels, name=f"{member.name.lower().replace(' ', '-')}-verification",
        )
        x = discord.Embed(
            title=f"Welcome to **{member.guild.name}**!",
            description=(
                f"Hey {member.mention}, welcome to the server!\n"
                f"Please use `{pre}verify` to verify. Enter the key you recieve in your DMs here."
            ),
            timestamp=datetime.datetime.utcnow(),
            color=discord.Color.green()
        )
        await channel.send(
            f"{member.mention}", embed=x,
            allowed_mentions=discord.AllowedMentions(
                users=True
            ),
        )

    # Leave Message
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        dchnl = discord.utils.get(member.guild.channels, name=f"{member.name.lower()}-verification")
        if dchnl in member.guild.channels:
            await dchnl.delete(reason=f"{member.name} left during verification process")

    async def check_if_mobile(self, member: discord.Member):
        return bool(member.is_on_mobile())

    @commands.command(brief="Verify now!", hidden=True)
    async def verify(self, ctx: AvimetryContext):
        member = ctx.author
        try:
            verify_config = ctx.cache.guild_settings["guild_id"]
        except KeyError:
            return await ctx.send("Verification has not been setup yet.")
        role_id = ctx.guild.get_role(verify_config["verify_role"])

        channel = discord.utils.get(
            ctx.guild.channels,
            name=f"{member.name.lower().replace(' ', '-')}-verification",
        )

        if not channel:
            return
        letters = string.ascii_letters
        randomkey = "".join(random.choice(letters) for i in range(10))

        try:
            rkey = discord.Embed()
            rkey.add_field(
                name="Here is your key. Your key will expire in 60 seconds.",
                value=f"`{randomkey}`",
            )
            if await self.check_if_mobile(member):
                await member.send("**Here is your key. Your key will expire in 1 minute.**")
                await member.send(f"{randomkey}")
            else:
                await member.send(embed=rkey)

        except discord.Forbidden:
            keyforbidden = discord.Embed()
            keyforbidden.add_field(
                name="Please turn on your DMs and run the `verify` command again.",
                value="User Settings > Privacy & Safety > Allow direct messages from server members",
            )
            return await ctx.send(embed=keyforbidden)

        ksid = discord.Embed(
            title="I sent a key to your DMs",
            description="Please enter your key here to complete the verification process."
        )
        await ctx.send(embed=ksid)
        channel = ctx.channel

        def check(m):
            return m.author == ctx.author and m.channel == channel

        try:
            msg = await self.avi.wait_for("message", timeout=60, check=check)
        except asyncio.TimeoutError:
            timeup = discord.Embed(
                title="Your Key has expired",
                description=(
                    "Sorry, your key has expired. If you want to generate a new key, "
                    f"use the command `{pre}.verify` to generate a new key."
                )
            )
            await ctx.author.send(embed=timeup)
        else:
            if msg.content != randomkey:
                await ctx.send("Wrong Key, Try again.")
            else:
                verembed = discord.Embed(
                    title="Verification complete!",
                    description="Congratulations, you have been verified! Please wait while I update your roles...",
                )
                await ctx.send(embed=verembed)
                await member.add_roles(role_id)
                cnl = discord.utils.get(
                    ctx.guild.channels, name=f"{member.name.lower().replace(' ', '-')}-verification",
                )
                try:
                    await cnl.delete(reason=f"{member.name} finished verification")
                except Exception:
                    pass


def setup(avi):
    avi.add_cog(MemberJoin(avi))
