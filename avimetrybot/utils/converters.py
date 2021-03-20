import re
import discord
from discord.ext import commands

time_regex = re.compile(r"(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


class TimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for key, value in matches:
            try:
                time += time_dict[value] * float(key)
            except KeyError:
                raise (commands.BadArgument(f"{key} is not a number!"))
        return round(time)


class TargetMemberAction(commands.Converter):
    async def convert(self, ctx, argument: discord.Member):
        try:
            member = await commands.MemberConverter().convert(ctx, argument)
        except Exception:
            member = await commands.UserConverter().convert(ctx, argument)

        if member == ctx.message.author:
            raise commands.BadArgument(f"You can not {ctx.invoked_with} yourself, That would be stupid.")

        if ctx.me.top_role < member.top_role:
            raise commands.BadArgument(
                f"I can not {ctx.invoked_with} them because their top role is higher than my top role."
            )

        if ctx.me.top_role == member.top_role:
            raise commands.BadArgument(
                f"I can't {ctx.invoked_with} {member} them because they have the same top role as me."
            )

        if member == ctx.me:
            raise commands.BadArgument(f"I can not {ctx.invoked_with} myself. Nice try.")

        if ctx.author.top_role < member.top_role:
            raise commands.BadArgument(
                f"You can't {ctx.invoked_with} {member} because their role is is higher than your role."
            )

        if ctx.author.top_role == member.top_role:
            raise commands.BadArgument(
                f"You can't {ctx.invoked_with} {member} because they have the same top role as you."
            )

        if member == ctx.guild.owner:
            raise commands.BadArgument(
                f"You can't {ctx.invoked_with} the server owner."
            )
        return member
