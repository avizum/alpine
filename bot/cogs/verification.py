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

    # Verification Gate
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        prefixes = await self.avi.temp.get_guild_settings(member.guild.id)
        global pre
        pre = prefixes["prefixes"][0] or "a."

        try:
            vergate = await self.avi.config.find(member.guild.id)
        except KeyError:
            return
        if vergate["verification_gate"] is False:
            return
        elif vergate["verification_gate"] is True:
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

    # Verify Command
    @commands.group(brief="Verify now!", invoke_without_command=True, hidden=True)
    async def verify(self, ctx: AvimetryContext):
        member = ctx.author
        get_role = await self.avi.config.find(ctx.guild.id)
        try:
            role = get_role["gate_role"]
        except KeyError:
            await ctx.send(
                "Verification has not been set up yet. You can enable it using the config command."
            )
            return
        roleid = ctx.guild.get_role(role)

        channel = discord.utils.get(
            ctx.guild.channels,
            name=f"{member.name.lower().replace(' ', '-')}-verification",
        )
        if not channel:
            fver = discord.Embed(
                title="You are already verified",
                description="Sorry, only people that are not verified can verify.",
            )
            await ctx.send(embed=fver)
        else:
            letters = string.ascii_letters
            randomkey = "".join(random.choice(letters) for i in range(10))
            if member.is_on_mobile():
                try:
                    await member.send(
                        "**Here is your key. Your key will expire in 1 minute.**"
                    )
                    await member.send(f"{randomkey}")
                except discord.Forbidden:
                    keyforbidden = discord.Embed()
                    keyforbidden.add_field(
                        name="Please turn on your DMs and run the `verify` command again.",
                        value="User Settings > Privacy & Safety > Allow direct messages from server members",
                    )
                    await ctx.send(embed=keyforbidden)
                    return
            else:
                try:
                    rkey = discord.Embed()
                    rkey.add_field(
                        name="Here is your key. Your key will expire in 60 seconds.",
                        value=f"`{randomkey}`",
                    )
                    await member.send(embed=rkey)
                except discord.Forbidden:
                    keyforbidden = discord.Embed()
                    keyforbidden.add_field(
                        name="Please turn on your DMs and run the `verify` command again.",
                        value="User Settings > Privacy & Safety > Allow direct messages from server members",
                    )
                    await ctx.send(embed=keyforbidden)
                    return

            ksid = discord.Embed(
                title="I sent a key to your DMs",
                description="Please enter your key here to complete the verification process."
            )
            await ctx.send(embed=ksid)
            channel = ctx.channel

            def check(m):
                return m.content == randomkey and m.channel == channel

            try:
                await self.avi.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                if member.is_on_mobile():
                    await member.send(
                        "<:noTick:777096756865269760> **Your Key has expired**\n"
                        "Sorry, your key has expired. If you want to generate a new key, "
                        "use the command `a.verify` to generate a new key."
                    )
                else:
                    timeup = discord.Embed(
                        title="Your Key has expired",
                        description=(
                            "Sorry, your key has expired. If you want to generate a new key, "
                            f"use the command `{pre}.verify` to generate a new key."
                        )
                    )
                    await ctx.author.send(embed=timeup)
            else:
                verembed = discord.Embed(
                    title="Verification complete!",
                    description="Congratulations, you have been verified! Please wait while I update your roles...",
                )
                await ctx.send(embed=verembed)
                await asyncio.sleep(0.5)
                await member.add_roles(roleid)
                await asyncio.sleep(2)
                cnl = discord.utils.get(
                    ctx.guild.channels, name=f"{member.name.lower().replace(' ', '-')}-verification",
                )
                try:
                    await cnl.delete(reason=f"{member.name} finished verification")
                except Exception:
                    pass

    @verify.command(hidden=True)
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def user(self, ctx: AvimetryContext, member: discord.Member):
        get_role = await self.avi.config.find(ctx.guild.id)
        try:
            role = get_role["gate_role"]
        except KeyError:
            await ctx.send(
                "The verification role has not been set. Use the config command to set it up."
            )
            return
        roleid = ctx.guild.get_role(role)
        if roleid in member.roles:
            await ctx.send("That member is already verified")
            return
        await member.add_roles(roleid)
        await ctx.send(f"{member} was manually verified")


def setup(avi):
    avi.add_cog(MemberJoin(avi))
