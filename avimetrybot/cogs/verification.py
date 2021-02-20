import discord
from discord.ext import commands
import string
import random
import asyncio


class Verification(commands.Cog):
    def __init__(self, avimetry):
        self.avimetry = avimetry

    # Verification Gate
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        prefixes = await self.avimetry.config.find(member.guild.id)
        global pre
        pre = prefixes["prefix"]

        if member.guild.id == (751490725555994716):
            channel = discord.utils.get(member.guild.channels, name="joins-and-leaves")

        if channel.guild.id == member.guild.id:
            join_message = discord.Embed(
                title="Member Joined",
                description=(
                    f"Hey **{str(member)}**, Welcome to **{member.guild.name}**!\n"
                    f"This server now has a total of **{member.guild.member_count}** members."
                ),
                color=discord.Color.blurple()
            )
            await channel.send(embed=join_message)

        try:
            vergate = await self.avimetry.config.find(member.guild.id)
        except KeyError:
            return
        if vergate["verification_gate"] is False:
            return
        elif vergate["verification_gate"] is True:
            name = "New Members"
            category = discord.utils.get(member.guild.categories, name=name)
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False
                ),
                member: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True, read_message_history=True
                ),
            }
            await member.guild.create_text_channel(
                f"{member.id}",
                category=category,
                reason=f"Started Verification for {member.name}",
                overwrites=overwrites,
            )

            channel = discord.utils.get(
                self.avimetry.get_all_channels(), name=f"{member.id}"
            )
            x = discord.Embed()
            x.add_field(
                name=f"Welcome to **{member.guild.name}**!",
                value=f"Hey, {member.mention}, welcome to **{member.guild.name}**! \n\nPlease read the rules over at the rules channel. After reading the rules, come back here to start the verification process. \n\nTo start the verification process, use the command `{pre}verify` \n\nYou will be given a randomly generated code to enter in this channel. **If you are on mobile, Please set your status to anything but `INVISIBLE`**",
            )
            await channel.send(f"{member.mention}", embed=x)
            try:
                y = discord.Embed()
                y.add_field(
                    name=f"Welcome to **{member.guild.name}**!",
                    value=f"Hey, {member.mention}, welcome to **{member.guild.name}**! \n\nPlease read the rules over at the rules channel. \n\nTo start the verification process, use the command `{pre}verify` in <#{channel.id}>.",
                )
                await member.send(f"{member.mention}", embed=y)
            except discord.Forbidden:
                return

    # Leave Message
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == (751490725555994716):
            channel = discord.utils.get(member.guild.channels, name="joins-and-leaves")
        if channel.guild.id == member.guild.id:
            lm = discord.Embed(
                title="Member Leave",
                description=(
                    f"Aww, **{str(member)}** has left **{member.guild.name}**.\n"
                    f"This server now has a total of **{member.guild.member_count}** members."
                ),
                color=discord.Color.red()
            )
            await channel.send(embed=lm)

        dchnl = discord.utils.get(self.avimetry.get_all_channels(), name=f"{member.id}")
        if dchnl in member.guild.channels:
            await dchnl.delete(reason=f"{member.name} left during verification process")

    # Verify Command
    @commands.group(brief="Verify now!", invoke_without_command=True, hidden=True)
    async def verify(self, ctx):
        member = ctx.author
        get_role = await self.avimetry.config.find(ctx.guild.id)
        try:
            role = get_role["gate_role"]
        except KeyError:
            await ctx.send(
                "The verification role has not been set. Please DM/contact staff in your server to fix this."
            )
            return
        roleid = ctx.guild.get_role(role)

        await ctx.message.delete()
        if roleid in member.roles:
            fver = discord.Embed()
            fver.add_field(
                name="<:noTick:777096756865269760> Already Verified",
                value="You are already verified!",
            )
            await (await ctx.send(embed=fver)).delete(delay=5)
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

            ksid = discord.Embed()
            ksid.add_field(
                name="<:yesTick:777096731438874634> A key was sent to your DMs",
                value="Enter your key here to get verified and have access to the channels.",
            )
            await ctx.send(embed=ksid)
            channel = ctx.channel

            def check(m):
                return m.content == randomkey and m.channel == channel

            try:
                await self.avimetry.wait_for("message", timeout=60, check=check)
            except asyncio.TimeoutError:
                if member.is_on_mobile():
                    await member.send(
                        "<:noTick:777096756865269760> **Your Key has expired**"
                        "Sorry, your key has expired. If you want to generate a new key, use the command `a.verify` to generate a new key."
                    )
                else:
                    timeup = discord.Embed()
                    timeup.add_field(
                        name="<:noTick:777096756865269760> Your Key has expired",
                        value="Sorry, your key has expired. If you want to generate a new key, use the command `a.verify` to generate a new key.",
                    )
                    await ctx.author.send(embed=timeup)
            else:
                verembed = discord.Embed()
                verembed.add_field(
                    name="<:yesTick:777096731438874634> Thank you",
                    value="You have been verified!",
                    inline=False,
                )
                await ctx.send(embed=verembed)
                await asyncio.sleep(0.5)
                await member.add_roles(roleid)
                await asyncio.sleep(2)
                cnl = discord.utils.get(
                    self.avimetry.get_all_channels(), name=f"{member.id}"
                )
                try:
                    await cnl.delete(reason=f"{member.name} finished verification")
                except Exception:
                    await ctx.send(
                        "Channel Delete failed, please contact a server staff member to delete this channel"
                    )

    @verify.command(hidden=True)
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def member(self, ctx, member: discord.Member):
        get_role = await self.avimetry.config.find(ctx.guild.id)
        try:
            role = get_role["gate_role"]
        except KeyError:
            await ctx.send(
                "The verification role has not been set. Use the config commaand to set it up."
            )
            return
        roleid = ctx.guild.get_role(role)
        if roleid in member.roles:
            await ctx.send("That member is already verified")
            return
        await member.add_roles(roleid)
        await ctx.send(f"{member} was manually verified")


def setup(avimetry):
    avimetry.add_cog(Verification(avimetry))
