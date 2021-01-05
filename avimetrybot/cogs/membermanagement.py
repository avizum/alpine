import discord
from discord.ext import commands

class Management(commands.Cog, name="Member Management"):
    def __init__(self, avimetry):
        self.avimetry=avimetry

#Counter
    @commands.Cog.listener()
    async def on_member_join(self, member):
        refchan = self.avimetry.get_channel(783961111060938782)
        if member.guild.id == refchan.guild.id:
            channel = self.avimetry.get_channel(783961111060938782)
            await channel.edit(name=f"Total Members: {member.guild.member_count}")
        
            channel2 = self.avimetry.get_channel(783960970472456232)
            true_member_count = len([m for m in member.guild.members if not m.bot])
            await channel2.edit(name=f"Members: {true_member_count}")

            channel3 = self.avimetry.get_channel(783961050814611476)
            true_bot_count = len([m for m in member.guild.members if m.bot])
            await channel3.edit(name=f"Bots: {true_bot_count}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        lrefchan = self.avimetry.get_channel(783961111060938782)
        if member.guild.id == lrefchan.guild.id:
            channel = self.avimetry.get_channel(783961111060938782)
            await channel.edit(name=f"Total Members: {member.guild.member_count}")
            
            channel2 = self.avimetry.get_channel(783960970472456232)
            true_member_count = len([m for m in member.guild.members if not m.bot])
            await channel2.edit(name=f"Members: {true_member_count}")

            channel3 = self.avimetry.get_channel(783961050814611476)
            true_bot_count = len([m for m in member.guild.members if m.bot])
            await channel3.edit(name=f"Bots: {true_bot_count}")
#Update Member Count Command
    @commands.command(aliases=["updatemc", "umembercount"], brief="Updates the member count if the count gets out of sync.")
    async def refreshcount(self, ctx):
        channel = self.avimetry.get_channel(783961111060938782)
        await channel.edit(name=f"Total Members: {channel.guild.member_count}")
        
        channel2 = self.avimetry.get_channel(783960970472456232)
        true_member_count = len([m for m in channel.guild.members if not m.bot])
        await channel2.edit(name=f"Members: {true_member_count}")

        channel3 = self.avimetry.get_channel(783961050814611476)
        true_bot_count = len([m for m in channel.guild.members if m.bot])
        await channel3.edit(name=f"Bots: {true_bot_count}")
        await ctx.send("Member Count Updated.")
        
#Member Count
    @commands.command(aliases=["members", "mc"], brief="Gets the members of the server and shows you.")
    async def membercount(self, ctx):
        tmc = len([m for m in ctx.guild.members if not m.bot])
        tbc = len([m for m in ctx.guild.members if m.bot])
        amc = ctx.guild.member_count
        mce = discord.Embed(title=f"Member Count for {ctx.guild.name}")
        mce.add_field(name="Members:", value=f"{tmc} members", inline=False)
        mce.add_field(name="Bots:", value=f"{tbc} bots", inline=False)
        mce.add_field(name="Total Members:", value=f"{amc} members", inline=False)
        await ctx.send(embed=mce)

#Role Command
    @commands.group(invoke_without_command=True, brief="Give or remove a role from a member.")
    @commands.has_permissions(kick_members=True)
    async def role(self, ctx):
        await ctx.send("Command: Role (work in progress)\n**add <member> <role>**\nGive a role to a member.\n\n**remove <member> <role>**\nRemove a role form a member.")

    @role.command(brief="Give a role to a member.")
    async def add(self, ctx, member:discord.Member, role:discord.Role):
        await member.add_roles(role)
        await ctx.send(f"added {role} to {member}")

    @role.command(brief="Remove a role from a member.")
    async def remove(self, ctx, member:discord.Member, role:discord.Role):
        await member.remove_roles(role)
        await ctx.send(f"removed {role} from {member}") 

#CNick Command
    @commands.command(brief="Changes a member's nickname.")
    @commands.has_permissions(kick_members=True)
    async def cnick(self, ctx, member: discord.Member, *,nick):
        if ctx.channel.id != 787942179310010368:
            await ctx.send("This command can only be used in <#787942179310010368>.")
        else:
            oldnick=member.display_name
            await member.edit(nick=nick)
            newnick=member.display_name
            nickembed=discord.Embed(title="<:aviSuccess:777096731438874634> Nickname Changed")
            nickembed.add_field(name="Old Nickname", value=f"{oldnick}", inline=True)
            nickembed.add_field(name="New Nickname", value=f"{newnick}", inline=True)
            await ctx.send(embed=nickembed)

#RNick Command
    @commands.command(brief="Restores a member's nick name to their username.")
    @commands.has_permissions(kick_members=True)
    async def rnick(self, ctx, member: discord.Member):
        nick=member.name
        oldnick=member.display_name
        await member.edit(nick=nick)
        newnick=member.display_name
        nickembed=discord.Embed(title="<:aviSuccess:777096731438874634> Restored Nickname")
        nickembed.add_field(name="Old Nickname", value=f"{oldnick}", inline=True)
        nickembed.add_field(name="New Nickname", value=f"{newnick}", inline=True)
        await ctx.send(embed=nickembed)

def setup(avimetry):
    avimetry.add_cog(Management(avimetry))