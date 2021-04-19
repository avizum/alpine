import discord
import asyncio
import datetime
import humanize
from discord.ext import commands
from utils.converters import TimeConverter, TargetMemberAction
from utils.context import AvimetryContext


class Moderation(commands.Cog):
    """
    Moderation commands.
    """
    def __init__(self, avi):
        self.avi = avi

    @commands.command(brief="Kicks a member from the server.", usage="<member> [reason]")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: AvimetryContext, member: TargetMemberAction, *, reason=None):
        if reason is None:
            reason = f"{ctx.author} ({ctx.author.id}): No reason was provided."
        else:
            reason = f"{ctx.author} ({ctx.author.id}): {reason}"
        kick_embed = discord.Embed(
            title="Kick Member"
        )
        try:
            dm_embed = discord.Embed(
                title="Moderation action: Kick",
                description=(
                    f"You were kicked from **{ctx.guild.name}** by **{ctx.author}**.\n"
                    f"Reason {reason}"
                ),
                timestamp=datetime.datetime.utcnow(),
            )
            await member.send(embed=dm_embed)
            await member.kick(reason=reason)
            kick_embed.description = f"**{member}** has been kicked from the server."
            await ctx.send(embed=kick_embed)
        except discord.HTTPException:
            await member.kick(reason=reason)
            kick_embed.description = f"**{member}** has been kicked from the server, but I could not DM them."
            await ctx.send(embed=kick_embed)

    @commands.command(brief="Bans a member from the server", usage="<member> [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: AvimetryContext, member: TargetMemberAction, *, reason=None):
        if reason is None:
            reason = f"{ctx.author} ({ctx.author.id}): No reason was provided."
        else:
            reason = f"{ctx.author} ({ctx.author.id}): {reason}"
        ban_embed = discord.Embed(
            title="Ban Member"
        )
        ban_embed.color = discord.Color.red()
        if isinstance(member, discord.User):
            ban_embed.color = discord.Color.green()
            await ctx.guild.ban(member, reason=reason)
            ban_embed.description = f"**{str(member)}** has been banned from the server."
            await ctx.send(embed=ban_embed)
        try:
            dm_embed = discord.Embed(
                title="Moderation action: Ban",
                description=(
                    f"You were banned from **{ctx.guild}** by **{ctx.author}**.\n"
                    f"**Reason:** {reason}"
                ),
                timestamp=datetime.datetime.utcnow(),
            )
            await member.send(embed=dm_embed)
            await member.ban(reason=reason)
            ban_embed.description = f"**{str(member)}** has been banned from the server."
            await ctx.send(embed=ban_embed)
        except discord.HTTPException:
            await member.ban(reason=reason)
            ban_embed.description = f"**{str(member)}** has been banned from the server, but I could not DM them."
            await ctx.send(embed=ban_embed)

    @commands.command(brief="Unbans a member from the server.", usage="<member_id> [reason]")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: AvimetryContext, member, *, reason="No reason was provided"):
        try:
            some_member = discord.Object(id=member)
            await ctx.guild.unban(some_member)
            unbanenmbed = discord.Embed()
            unbanenmbed.add_field(
                name="<:yesTick:777096731438874634> Unban Member",
                value=f"Unbanned <@{member}> ({member}) from **{ctx.guild.name}**.",
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

    @commands.command()
    async def mute(self, ctx: AvimetryContext, member: TargetMemberAction, duration: TimeConverter, reason=None):
        if reason is None:
            reason = f"{ctx.author} ({ctx.author.id}): No reason was provided."
        else:
            reason = f"{ctx.author} ({ctx.author.id}): {reason}"
        role = await ctx.cache.get_guild_settings(ctx.guild.id)
        mute_role = ctx.guild.get_role(role["mute_role"])
        await member.add_roles(mute_role, reason=reason)

    @commands.group(
        invoke_without_command=True,
        brief="Delete a number of messages in the current channel.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.cooldown(5, 30, commands.BucketType.member)
    async def purge(self, ctx: AvimetryContext, amount: int):
        await ctx.message.delete()
        if amount > 1:
            return
        authors = {}
        async for message in ctx.channel.history(limit=amount):
            if message.author not in authors:
                authors[message.author] = 1
            else:
                authors[message.author] += 1
        await asyncio.sleep(0.1)
        await ctx.channel.purge(limit=amount)
        msg = "\n".join(
            f"{author.mention}: {amount} {'message' if amount==1 else 'messages'}"
            for author, amount in authors.items()
        )

        pe = discord.Embed(
            title="Affected Messages",
            description=f"{msg}"
        )
        await ctx.send(embed=pe, delete_after=10)

    @purge.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def match(self, ctx: AvimetryContext, amount: int, *, text):
        await ctx.message.delete()

        def pmatch(m):
            return text in m.content

        await ctx.channel.purge(limit=amount, check=pmatch)
        purgematch = discord.Embed()
        purgematch.add_field(
            name="<:yesTick:777096731438874634> Purge Match",
            value=f"Purged {amount} messages containing {text}.",
        )

    @commands.command(brief="Cleans bot messages", usage="[amount]")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def cleanup(self, ctx: AvimetryContext, amount=15):
        try:
            await ctx.message.delete()
        except Exception:
            pass
        authors = {}
        messages = []
        async for message in ctx.channel.history(limit=amount*2):
            check_prefix = await ctx.cache.get_guild_settings(ctx.guild.id)
            prefixes = tuple(check_prefix["prefixes"])
            if message.author == self.avi.user or message.content.lower().startswith(prefixes):
                if message.author not in authors:
                    authors[message.author] = 1
                else:
                    authors[message.author] += 1
                messages.append(message)
                if len(messages) == amount:
                    break
        await ctx.channel.delete_messages(messages)
        msg = "\n".join(
            f"{author.mention}: {amount} {'message' if amount==1 else 'messages'}"
            for author, amount in authors.items()
        )

        pe = discord.Embed(
            title="Affected Messages",
            description=f"{msg}"
        )
        await ctx.send(embed=pe, delete_after=10)

    @commands.command(
        brief="Locks the mentioned channel.",
        usage="<channel> [reason]",
        timestamp=datetime.datetime.utcnow())
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx: AvimetryContext, channel: discord.TextChannel, *, reason="No Reason Provided"):
        await channel.set_permissions(
            ctx.guild.default_role, send_messages=False,
        )
        lc = discord.Embed()
        lc.add_field(
            name=":lock: Channel has been locked.",
            value=f"{ctx.author.mention} has locked down <#{channel.id}> with the reason of {reason}. \
            Only Staff members can speak now.",
        )
        await channel.send(embed=lc)

    @commands.command(
        brief="Unlocks the mentioned channel.",
        usage="<channel> [reason]",
        timestamp=datetime.datetime.utcnow(),
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx: AvimetryContext, channel: discord.TextChannel, *, reason="No Reason Provided"):
        await channel.set_permissions(
            ctx.guild.default_role, send_messages=None)
        uc = discord.Embed()
        uc.add_field(
            name=":unlock: Channel has been unlocked.",
            value=f"{ctx.author.mention} has unlocked <#{channel.id}> with the reason of {reason}. \
            Everyone can speak now.",
        )
        await channel.send(embed=uc)

    @commands.command(brief="Sets the slowmode in the current channel.")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: AvimetryContext, *, seconds: TimeConverter = None):
        if seconds > 21600:
            raise commands.BadArgument("Amount should be less than or equal to 6 hours")
        await ctx.channel.edit(slowmode_delay=seconds)
        smembed = discord.Embed()
        smembed.add_field(
            name="<:yesTick:777096731438874634> Set Slowmode",
            value=f"Slowmode delay is now set to {humanize.precisedelta(seconds)}.",
        )
        await ctx.send(embed=smembed)

    @commands.group(invoke_without_command=True, brief="The command you just called")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx: AvimetryContext):
        await ctx.send_help("role")

    @role.command(brief="Give a role to a member.")
    async def add(self, ctx: AvimetryContext, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        ra = discord.Embed()
        ra.add_field(
            name="<:yesTick:777096731438874634> Role Add",
            value=f"Added {role.mention} to {member.mention}.",
        )
        await ctx.send(embed=ra)

    @role.command(brief="Remove a role from a member.")
    async def remove(self, ctx: AvimetryContext, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        rr = discord.Embed()
        rr.add_field(
            name="<:yesTick:777096731438874634> Role Remove",
            value=f"Removed {role.mention} from {member.mention}",
        )
        await ctx.send(embed=rr)

    @commands.command(brief="Changes a member's nickname.")
    @commands.has_permissions(kick_members=True)
    async def nick(self, ctx: AvimetryContext, member: discord.Member, *, nick=None):
        if nick is None:
            await member.edit(nick=nick)
        oldnick = member.display_name
        await member.edit(nick=nick)
        newnick = member.display_name
        nickembed = discord.Embed(
            title="<:yesTick:777096731438874634> Nickname Changed"
        )
        nickembed.add_field(name="Old Nickname", value=f"{oldnick}", inline=True)
        nickembed.add_field(name="New Nickname", value=f"{newnick}", inline=True)
        await ctx.send(embed=nickembed)


def setup(avi):
    avi.add_cog(Moderation(avi))
