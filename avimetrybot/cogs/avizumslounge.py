import discord
from discord.ext import commands
from utils.errors import AvizumsLoungeOnly


class AvizumsLounge(commands.Cog, name="Avizum's Lounge"):
    def __init__(self, avi):
        self.avi = avi

    def cog_check(self, ctx):
        if ctx.guild.id != 751490725555994716:
            raise AvizumsLoungeOnly("This command only works in a private server.")
        return True

    # Counter
    @commands.Cog.listener()
    async def on_member_join(self, member):

        if member.guild.id == (751490725555994716):
            channel = discord.utils.get(member.guild.channels, name="joins-and-leaves")
            root = member.guild.get_role(813535792655892481)
            await member.add_roles(root)

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

        refchan = self.avi.get_channel(783961111060938782)
        try:
            if member.guild.id == refchan.guild.id:
                channel = self.avi.get_channel(783961111060938782)
                await channel.edit(name=f"Total Members: {member.guild.member_count}")

                channel2 = self.avi.get_channel(783960970472456232)
                true_member_count = len([m for m in member.guild.members if not m.bot])
                await channel2.edit(name=f"Members: {true_member_count}")

                channel3 = self.avi.get_channel(783961050814611476)
                true_bot_count = len([m for m in member.guild.members if m.bot])
                await channel3.edit(name=f"Bots: {true_bot_count}")
        except Exception:
            return

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

        lrefchan = self.avi.get_channel(783961111060938782)
        try:
            if member.guild.id == lrefchan.guild.id:
                channel = self.avi.get_channel(783961111060938782)
                await channel.edit(name=f"Total Members: {member.guild.member_count}")

                channel2 = self.avi.get_channel(783960970472456232)
                true_member_count = len([m for m in member.guild.members if not m.bot])
                await channel2.edit(name=f"Members: {true_member_count}")

                channel3 = self.avi.get_channel(783961050814611476)
                true_bot_count = len([m for m in member.guild.members if m.bot])
                await channel3.edit(name=f"Bots: {true_bot_count}")
        except Exception:
            return

    @commands.Cog.listener("on_voice_state_update")
    async def vs_update(self, member, before, after):
        if member.guild.id != 751490725555994716:
            return
        try:
            if after.channel is None:
                channel = discord.utils.get(member.guild.text_channels, name=f"vc-{before.channel.name}")
                await channel.set_permissions(member, overwrite=None)
                return
            else:
                if before.channel:
                    before_channel = discord.utils.get(member.guild.text_channels, name=f"vc-{before.channel.name}")
                    await before_channel.set_permissions(member, overwrite=None)

                channel = discord.utils.get(member.guild.text_channels, name=f"vc-{after.channel.name}")
                if channel is None:
                    return

                if after.channel.name == channel.name[3:]:
                    overwrites = discord.PermissionOverwrite()
                    overwrites.read_messages = True
                    overwrites.read_message_history = True
                    await channel.set_permissions(member, overwrite=overwrites)

        except Exception:
            return

    # Update Member Count Command
    @commands.command(
        aliases=["updatemc", "umembercount"],
        brief="Updates the member count if the count gets out of sync.",
    )
    @commands.has_permissions(administrator=True)
    async def refreshcount(self, ctx):
        channel = self.avi.get_channel(783961111060938782)
        await channel.edit(name=f"Total Members: {channel.guild.member_count}")

        channel2 = self.avi.get_channel(783960970472456232)
        true_member_count = len([m for m in channel.guild.members if not m.bot])
        await channel2.edit(name=f"Members: {true_member_count}")

        channel3 = self.avi.get_channel(783961050814611476)
        true_bot_count = len([m for m in channel.guild.members if m.bot])
        await channel3.edit(name=f"Bots: {true_bot_count}")
        await ctx.send("Member Count Updated.")

    # Self Nick
    @commands.command(aliases=["snick"], brief="Changes your nick name")
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 600, commands.BucketType.member)
    async def selfnick(self, ctx, *, nick):
        oldnick = ctx.author.display_name
        if ctx.guild.id == 751490725555994716:
            if "avi" in nick.lower():
                return await ctx.send("You can not have your nickname as avi")
        await ctx.author.edit(nick=nick)
        newnick = ctx.author.display_name
        nickembed = discord.Embed(
            title="<:yesTick:777096731438874634> Nickname Changed"
        )
        nickembed.add_field(name="Old Nickname", value=f"{oldnick}", inline=True)
        nickembed.add_field(name="New Nickname", value=f"{newnick}", inline=True)
        await ctx.send(embed=nickembed)


def setup(avi):
    avi.add_cog(AvizumsLounge(avi))
