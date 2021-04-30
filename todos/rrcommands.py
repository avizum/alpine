import discord
from discord.ext import commands
from utils.context import AvimetryContext


# rr
@commands.command()
async def rr(self, ctx: AvimetryContext):
    embed = discord.Embed(
        title="Reaction Roles",
        description=(
            "React with the emojis below to get your roles.\n"
            "<:announceping:828446615135191100> | <@&828437716429570128>\n"
            "<:updateping:828445765772509234> | <@&828437885820076053>"),
        color=discord.Color.blurple()
    )
    message = await ctx.send_raw(embed=embed)
    await message.add_reaction("<:announceping:828446615135191100>")
    await message.add_reaction("<:updateping:828445765772509234>")
    embed = discord.Embed(
        title="Color Roles I",
        description=(
            "Do not spam the reactions, You will be blacklisted if you are caught.\nHave fun!\n"
            "<:Black:828803461499322419> | <@&828783285735653407>\n"
            "<:Blue:828803483456897064> | <@&828783291603746877>\n"
            "<:Blurple:828803502284472330> | <@&828467481236078622>\n"
            "<:Cyan:828803518751047760> | <@&828783292924297248>\n"
            "<:Gold:828803535088386080> | <@&828783296983990272>\n"
            "<:Gray:828803555192078416> | <@&828716599950311426>\n"
            "<:Green:828803571566248008> | <@&828783295382814750>\n"
            "<:HSBalance:828803590067322910> | <@&828788247105765407>\n"
            "<:HSBravery:828803604839792661> | <@&828788233327869994>\n"
            "<:HSBrilliance:828803624644771860> | <@&828788255334858815>\n"
            "<:Magenta:828803640004837376> | <@&828783290281754664>\n"
            "<:Mint:828803656924397589> | <@&828783293699850260>\n"
            ),
        color=discord.Color.blurple()
    )
    message = await ctx.send_raw(embed=embed)
    await message.add_reaction("<:Black:828803461499322419>")
    await message.add_reaction("<:Blue:828803483456897064>")
    await message.add_reaction("<:Blurple:828803502284472330>")
    await message.add_reaction("<:Cyan:828803518751047760>")
    await message.add_reaction("<:Gold:828803535088386080>")
    await message.add_reaction("<:Gray:828803555192078416>")
    await message.add_reaction("<:Green:828803571566248008>")
    await message.add_reaction("<:HSBalance:828803590067322910>")
    await message.add_reaction("<:HSBravery:828803604839792661>")
    await message.add_reaction("<:HSBrilliance:828803624644771860>")
    await message.add_reaction("<:Magenta:828803640004837376>")
    await message.add_reaction("<:Mint:828803656924397589>")
    embeed = discord.Embed(
        title="Color Roles II",
        description=(
            "Do not spam the reactions, You will be blacklisted if you are caught.\nHave fun!\n"
            "<:Orange:828803674633011253> | <@&828783297411678240>\n"
            "<:Pink:828803726089256991> | <@&828783289400950864>\n"
            "<:Purple:828803747755851776> | <@&828783291279867934>\n"
            "<:Red:828803769013370880> | <@&828783297927839745>\n"
            "<:Salmon:828803790673018960> | <@&828783288410832916>\n"
            "<:Silver:828803810533179404> | <@&828783286599024671>\n"
            "<:Sky:828803838387290162> | <@&828783292504604702>\n"
            "<:Tan:828803863661248513> | <@&828783287585341470>\n"
            "<:Teal:828803885811367966> | <@&828448876469026846>\n"
            "<:USNavyBlue:828803903637422100> | <@&828799927857053696>\n"
            "<:White:828803923799179304> | <@&828476018439356436>\n"
            "<:Yellow:828803974941245470> | <@&828783296023625770>"
        ),
        color=discord.Color.blurple()
    )
    mmessage = await ctx.send_raw(embed=embeed)
    await mmessage.add_reaction("<:Orange:828803674633011253>")
    await mmessage.add_reaction("<:Pink:828803726089256991>")
    await mmessage.add_reaction("<:Purple:828803747755851776>")
    await mmessage.add_reaction("<:Red:828803769013370880>")
    await mmessage.add_reaction("<:Salmon:828803790673018960>")
    await mmessage.add_reaction("<:Silver:828803810533179404>")
    await mmessage.add_reaction("<:Sky:828803838387290162>")
    await mmessage.add_reaction("<:Tan:828803863661248513>")
    await mmessage.add_reaction("<:Teal:828803885811367966>")
    await mmessage.add_reaction("<:USNavyBlue:828803903637422100>")
    await mmessage.add_reaction("<:White:828803923799179304>")
    await mmessage.add_reaction("<:Yellow:828803974941245470>")
