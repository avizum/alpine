import discord
from discord.ext import commands, tasks
from copy import deepcopy
from dateutil.relativedelta import relativedelta
import asyncio
import datetime
import humanize
from utils.converters import TimeConverter
import typing


class Moderation(commands.Cog):
    """
    Moderation commands.
    """
    def __init__(self, avimetry):
        self.avimetry = avimetry
        self.check_mutes.start()

    def cog_unload(self):
        self.check_mutes.cancel()

    # Unmute Loop
    @tasks.loop(minutes=1)
    async def check_mutes(self):
        current_time = datetime.datetime.now()
        mutes = deepcopy(self.avimetry.muted_users)
        for key, value in mutes.items():
            if value["mute_duration"] is None:
                continue

            unmute_time = value["muted_at"] + relativedelta(seconds=value["mute_duration"])

            if current_time >= unmute_time:
                guild = self.avimetry.get_guild(value["guild_id"])
                member = guild.get_member(value["_id"])

                role = discord.utils.get(guild.roles, name="Muted")
                if role in member.roles:
                    await member.remove_roles(role)
                    try:
                        unmuted = discord.Embed()
                        unmuted.add_field(
                            name="<:yesTick:777096731438874634> Unmuted",
                            value=f"You have been unmuted in {member.guild.name}",
                        )
                        await member.send(embed=unmuted)
                    except discord.Forbidden:
                        return
                else:
                    try:
                        await self.avimetry.mutes.delete(member.id)
                        await self.avimetry.muted_users.pop(member.id)
                    except discord.Forbidden:
                        return
                await self.avimetry.mutes.delete(member.id)
                try:
                    self.avimetry.muted_users.pop(member.id)
                except KeyError:
                    pass

    @check_mutes.before_loop
    async def before_check_mutes(self):
        await self.avimetry.wait_until_ready()

    # Clean Command
    @commands.command(brief="Cleans bot messages", usage="[amount]")
    @commands.has_permissions(manage_messages=True)
    async def clean(self, ctx, amount=15, limit=100):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        message_list = []
        msg_count = 0
        async for message in ctx.channel.history(limit=limit):
            if message.author.id == self.avimetry.user.id:
                message_list.append(message)
                msg_count += 1
                if msg_count >= amount:
                    break
            if message.content.lower().startswith(ctx.clean_prefix):
                message_list.append(message)
        try:
            await ctx.channel.delete_messages(message_list)
        except Exception:
            for mes in message_list:
                await mes.delete()
        clean_embed = discord.Embed(
            title="Clean Messages",
            description=f"Successfully deleted {msg_count} messages."
        )
        await ctx.send(embed=clean_embed)

    # Purge Command
    @commands.group(
        invoke_without_command=True,
        brief="Delete a number of messages in the current channel.",
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(5, 30, commands.BucketType.member)
    async def purge(self, ctx, amount: int):
        await ctx.message.delete()
        if amount == 0:
            pass
        elif amount > 250:
            a100 = discord.Embed()
            a100.add_field(
                name="<:noTick:777096756865269760> No Permission",
                value="You can't purge more than 150 messages at a time.",
            )
            await ctx.send(embed=a100, delete_after=10)
        else:
            authors = {}
            async for message in ctx.channel.history(limit=amount):
                if message.author not in authors:
                    authors[message.author] = 1
                else:
                    authors[message.author] += 1
            await asyncio.sleep(0.1)
            purge_amount = await ctx.channel.purge(limit=amount)
            msg = "\n".join(
                [f"{author}: {amount}" for author, amount in authors.items()]
            )

            pe = discord.Embed()
            pe.add_field(
                name="<:yesTick:777096731438874634> Purge Messages",
                value=(
                    f"Here are the results of the purged messages"
                    f"\n`{msg}`\n\n Total Messages Deleted:`{len(purge_amount)}`"
                ),
            )
            await ctx.send(embed=pe, delete_after=10)

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def match(self, ctx, amount: int, *, text):
        await ctx.message.delete()

        def pmatch(m):
            return text in m.content

        await ctx.channel.purge(limit=amount, check=pmatch)
        purgematch = discord.Embed()
        purgematch.add_field(
            name="<:yesTick:777096731438874634> Purge Match",
            value=f"Purged {amount} messages containing {text}.",
        )

    # Lock Channel Command
    @commands.command(
        brief="Locks the mentioned channel.",
        usage="<channel> [reason]",
        timestamp=datetime.datetime.utcnow(),
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(
        self, ctx, channel: discord.TextChannel, *, reason="No Reason Provided"
    ):
        await channel.set_permissions(
            ctx.guild.default_role, send_messages=False, read_messages=False
        )
        lc = discord.Embed()
        lc.add_field(
            name=":lock: Channel has been locked.",
            value=f"{ctx.author.mention} has locked down <#{channel.id}> with the reason of {reason}. \
            Only Staff members can speak now.",
        )
        await channel.send(embed=lc)

    # Unlock Channel command
    @commands.command(
        brief="Unlocks the mentioned channel.",
        usage="<channel> [reason]",
        timestamp=datetime.datetime.utcnow(),
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(
        self, ctx, channel: discord.TextChannel, *, reason="No Reason Provided"
    ):
        await channel.set_permissions(
            ctx.guild.default_role, send_messages=None, read_messages=False
        )
        uc = discord.Embed()
        uc.add_field(
            name=":unlock: Channel has been unlocked.",
            value=f"{ctx.author.mention} has unlocked <#{channel.id}> with the reason of {reason}. \
            Everyone can speak now.",
        )
        await channel.send(embed=uc)

    # Kick Command
    @commands.command(
        brief="Kicks a member from the server.", usage="<member> [reason]"
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        if reason is None:
            reason = f"{ctx.author} ({ctx.author.id}): No reason was provided."
        else:
            reason = f"{ctx.author} ({ctx.author.id}): {reason}"
        kick_embed = discord.Embed(
            title="Kick Member"
        )
        if member == ctx.message.author:
            kick_embed.description = "You can not kick yourself, That would be stupid."
            return await ctx.send(embed=kick_embed, delete_after=10)
        elif member == self.avimetry.user:
            kick_embed.description = "You can not kick me because I can't kick myself."
            return await ctx.send(embed=kick_embed, delete_after=10)
        elif ctx.author.top_role <= member.top_role:
            kick_embed.description = "You can not kick someone with a role equal or greater than your role"
            return await ctx.send(embed=kick_embed, delete_after=10)
        else:
            try:
                dm_embed = discord.Embed(
                    title="Moderation action: Kick",
                    description=f"You were kicked from **{ctx.guild.name}** by **{ctx.author}**",
                    timestamp=datetime.datetime.utcnow(),
                )
                await member.send(embed=dm_embed)
                await member.kick(reason=reason)
                kick_embed.description = f"**{str(member)}** has been kicked from the server."
                await ctx.send(embed=kick_embed)
            except discord.HTTPException:
                await member.kick(reason=reason)
                kick_embed.description = f"**{str(member)}** has been kicked from the server, but I could not DM them.",
                await ctx.send(embed=kick_embed)

    # Ban Command
    @commands.command(brief="Bans a member from the server", usage="<member> [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: typing.Union[discord.User, discord.Member], *, reason=None):
        if reason is None:
            reason = f"{ctx.author} ({ctx.author.id}): No reason was provided."
        else:
            reason = f"{ctx.author} ({ctx.author.id}): {reason}"
        ban_embed = discord.Embed(
            title="Ban Member"
        )
        ban_embed.color = discord.Color.red()
        if member == ctx.message.author:
            ban_embed.description = "You can not ban yourself, That would be stupid."
            return await ctx.send(embed=ban_embed, delete_after=10)
        elif member == self.avimetry.user:
            ban_embed.description = "You can not ban me because I can't kick myself."
            return await ctx.send(embed=ban_embed, delete_after=10)
        elif ctx.author.top_role <= member.top_role:
            ban_embed.description = "You can not ban someone with a role equal or greater than your role"
            return await ctx.send(embed=ban_embed, delete_after=10)
        else:
            ban_embed.color = discord.Color.green()
            try:
                dm_embed = discord.Embed(
                    title="Moderation action: Ban",
                    description=f"You were banned from **{ctx.guild}** by **{ctx.author}**",
                    timestamp=datetime.datetime.utcnow(),
                )
                await member.send(embed=dm_embed)
                # await member.ban(reason=reason)
                ban_embed.description = f"**{str(member)}** has been banned from the server."
                await ctx.send(embed=ban_embed)
            except discord.HTTPException:
                # await member.ban(reason=reason)
                ban_embed.description = f"**{str(member)}** has been banned from the server, but I could not DM them.",
                await ctx.send(embed=ban_embed)

    # Unban Command
    @commands.command(
        brief="Unbans a member from the server.", usage="<member_id> [reason]"
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, member, *, reason="No reason was provided"):
        try:
            some_member = discord.Object(id=member)
            await ctx.guild.unban(some_member)
            unbanenmbed = discord.Embed()
            unbanenmbed.add_field(
                name="<:yesTick:777096731438874634> Unban Member",
                value="Unbanned <@{member}> ({member}) from **{ctx.guild.name}**.",
                inline=False,
            )
            await ctx.send(embed=unbanenmbed)
        except Exception:
            banned_users = await ctx.guild.bans()
            member_name, member_discriminator = member.split("#")
            for ban_entry in banned_users:
                user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                unbanenmbed = discord.Embed()
                unbanenmbed.add_field(
                    name="<:yesTick:777096731438874634> Unban Member",
                    value=f"Unbanned **{member}** from **{ctx.guild.name}**.",
                    inline=False,
                )
                await ctx.send(embed=unbanenmbed)
        else:
            await ctx.send("Unban failed")

    # Slowmode Command
    @commands.command(brief="Sets the slowmode in the current channel.")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx, *, seconds: TimeConverter = None):
        if seconds > 21600:
            raise commands.BadArgument("Amount should be less than or equal to 6 hours")
        await ctx.channel.edit(slowmode_delay=seconds)
        smembed = discord.Embed()
        smembed.add_field(
            name="<:yesTick:777096731438874634> Set Slowmode",
            value=f"Slowmode delay is now set to {humanize.precisedelta(seconds)}.",
        )
        await ctx.send(embed=smembed)

    # Mute command
    @commands.command(brief="Mutes a member.")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, time: TimeConverter = None):
        if time is None:
            pass
        elif time < 300:
            return await ctx.send("The minumum mute time is 5 minutes.")
        elif time > 604800:
            return await ctx.send("The maximum mute time is 7 days.")
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            no_muted_role = discord.Embed()
            no_muted_role.add_field(
                name="<:noTick:777096756865269760> Mute Failed",
                value=f"Couldn't mute {member.mention} because there is no muted role.",
            )
            await ctx.send(embed=no_muted_role)
            return
        try:
            if self.avimetry.muted_users[member.id]:
                already_muted = discord.Embed()
                already_muted.add_field(
                    name="<:noTick:777096756865269760> Mute Failed",
                    value=f"{member.mention} is already muted",
                )
                await ctx.send(embed=already_muted)
            return
        except KeyError:
            pass
        data = {
            "_id": member.id,
            "muted_at": datetime.datetime.now(),
            "mute_duration": time or None,
            "moderator": ctx.author.id,
            "guild_id": ctx.guild.id,
        }
        await self.avimetry.mutes.upsert(data)
        self.avimetry.muted_users[member.id] = data
        await member.add_roles(role)
        if not time:
            unlimited_mute = discord.Embed()
            unlimited_mute.add_field(
                name="<:yesTick:777096731438874634> Muted Member",
                value=f"{member.mention} was muted with no unmute time.",
            )
            await ctx.send(embed=unlimited_mute)
        else:
            mute_embed = discord.Embed(
                title="Member Muted",
                description=f"{member.mention} has been muted for {humanize.naturaldelta(time)}"
            )
            await ctx.send(embed=mute_embed)

        if time and time < 300:
            await asyncio.sleep(time)
            if role in member.roles:
                await member.remove_roles(role)
                try:
                    unmuted = discord.Embed()
                    unmuted.add_field(
                        name="<:yesTick:777096731438874634> Unmuted",
                        value=f"You have been unmuted in {member.guild.name}",
                    )
                    await member.send(embed=unmuted)
                except discord.Forbidden:
                    return
            await self.avimetry.mutes.delete(member.id)
            try:
                self.avimetry.muted_users.pop(member.id)
            except KeyError:
                pass

    # Unmute command
    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def unmute(self, ctx, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not role:
            await ctx.send("No role named muted")
            return

        await self.avimetry.mutes.delete(member.id)
        try:
            self.avimetry.muted_users.pop(member.id)
        except KeyError:
            pass
        if role not in member.roles:
            await ctx.send("This member is not muted")
            return

        await member.remove_roles(role)
        await ctx.send(f"Unmuted {member.display_name}")

    # Role Command
    @commands.group(invoke_without_command=True, brief="The command you just called")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx):
        await ctx.send_help("role")

    @role.command(brief="Give a role to a member.")
    async def add(self, ctx, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        ra = discord.Embed()
        ra.add_field(
            name="<:yesTick:777096731438874634> Role Add",
            value=f"Added {role.mention} to {member.mention}.",
        )
        await ctx.send(embed=ra)

    @role.command(brief="Remove a role from a member.")
    async def remove(self, ctx, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        rr = discord.Embed()
        rr.add_field(
            name="<:yesTick:777096731438874634> Role Remove",
            value=f"Removed {role.mention} from {member.mention}",
        )
        await ctx.send(embed=rr)

    # Nick Command
    @commands.command(brief="Changes a member's nickname.")
    @commands.has_permissions(kick_members=True)
    async def nick(self, ctx, member: discord.Member, *, nick=None):
        if nick is None:
            await member.edit(nick=member.name)
        oldnick = member.display_name
        await member.edit(nick=nick)
        newnick = member.display_name
        nickembed = discord.Embed(
            title="<:yesTick:777096731438874634> Nickname Changed"
        )
        nickembed.add_field(name="Old Nickname", value=f"{oldnick}", inline=True)
        nickembed.add_field(name="New Nickname", value=f"{newnick}", inline=True)
        await ctx.send(embed=nickembed)


def setup(avimetry):
    avimetry.add_cog(Moderation(avimetry))
