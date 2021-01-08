import discord
from discord.ext import commands
import random
import datetime
import json

class BotLogs(commands.Cog, name="Bot Logs"):

    def __init__(self, avimetry):
        self.avimetry = avimetry
    '''
#Message Logger
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        with open("./avimetrybot/files/bot-logs.json", "r") as f:
            msglogger = json.load(f)
            if str(message.guild.id) in msglogger:
                if msglogger[str(message.guild.id)] == 0:
                    return
                elif msglogger[str(message.guild.id)] == 1:
                    with open("./avimetrybot/files/prefixes.json", "r") as f:
                        prefixes = json.load(f)
                    pre = prefixes[str(message.guild.id)]
                    if message.guild is None:
                        return
                    if message.author == self.avimetry.user:
                        return
                    if message.content == '<@!756257170521063444>':
                        a = discord.Embed(title=f"{self.avimetry.user.name} Info", description=f"Hey, my prefix for **{message.guild.name}** is `{pre}` \nIf you need help, use `{pre}help`")
                        await message.reply(embed=a)
                    elif message.author.bot:
                        return
                    elif message.channel == discord.utils.get(self.avimetry.get_all_channels(), name='verify'):
                        return
                    elif message.channel == discord.utils.get(self.avimetry.get_all_channels(), name='counting'):
                        return
                    elif message.content.startswith(pre):
                        return
                    elif message.attachments:
                        channel = discord.utils.get(self.avimetry.get_all_channels(),  name='chat-logs')
                        mcontent=message.attachments[0].url
                        embed=discord.Embed(title=f"Image from {message.author}, Server {message.guild}", timestamp=datetime.datetime.utcnow())
                        embed.set_image(url=f'{mcontent}')
                        await channel.send(embed=embed)
                    elif message.content:
                        channel = discord.utils.get(self.avimetry.get_all_channels(),  name='chat-logs')
                        mcontent=message.content
                        embed=discord.Embed(title=f"Message from {message.author}", description=f"<#{message.channel.id}>\n`{mcontent}`",timestamp=datetime.datetime.utcnow())
                        await channel.send(embed=embed) 
                else:
                    msglogger[str(message.guild.id)] = 0
                    with open("./avimetrybot/files/bot-logs.json", "w") as f:
                        json.dump(msglogger, f, indent=4)
                                            
#Message Edit
    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        if message_after.guild is None and message_after.guild is None:
            return
        channel = discord.utils.get(self.avimetry.get_all_channels(), name='bot-logs')
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        pre = prefixes[str(message_after.guild.id)]
        if message_before.author == self.avimetry.user:
            return
        elif message_before.content.startswith(pre):
            return
        elif message_after.content.startswith(pre):
            return
        elif message_before.channel == discord.utils.get(self.avimetry.get_all_channels(), name='verify'):
            return 
        elif message_before.channel == discord.utils.get(self.avimetry.get_all_channels(), name='counting'):
            return
        elif message_before.author.bot:
            return
        elif message_before.attachments:
             return
        else:
            try:
                editembed=discord.Embed(title='Message Edit', description=f'A message from {message_before.author.mention} was edited. Information is below.')
                editembed.add_field(name='Original Message:', value=f'`{message_before.content}`', inline=False)
                editembed.add_field(name='Edited Message:', value=f'`{message_after.content}`', inline=False)
                await channel.send(embed=editembed)
            except discord.HTTPException:
                editembed2=discord.Embed(title='Message Edit', description=f'A message from {message_before.author.mention} was edited. Information is below.')
                editembed2.add_field(name='Original Message Error:', value="Message is too long", inline=False)
                editembed2.add_field(name='Edited Message Error:', value="Message is too long", inline=False)
                await channel.send(embed=editembed2)

#Message Delete
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None:
            return
        channel = discord.utils.get(self.avimetry.get_all_channels(), name='bot-logs')
        with open("./avimetrybot/files/prefixes.json", "r") as f:
            prefixes = json.load(f)
        pre = prefixes[str(message.guild.id)]
        if message.channel == discord.utils.get(self.avimetry.get_all_channels(), name='verify'):
            return
        elif message.channel == discord.utils.get(self.avimetry.get_all_channels(), name='counting'):
            return
        elif message.author.bot:
            return
        elif message.author == self.avimetry.user:
            return
        elif message.content.startswith(pre):
            return
        elif message.attachments:
            pdelembed=discord.Embed(title='Message Delete', description=f'An image from {message.author.mention} was deleted. Information is below.')
            pdelembed.add_field(name='Message Delete', value=f'An attachment from {message.author.mention} was deleted. However, deleted messages can not be logged.', inline=False)
            await channel.send(embed=pdelembed)
        else:
            try:
                delembed=discord.Embed(title='Message Delete', description=f'A message from {message.author.mention} was deleted. The deleted message is below.')
                delembed.add_field(name='Deleted Message:', value=f'`{message.content}`', inline=False)
                await channel.send(embed=delembed)
            except discord.HTTPException:
                delembed2=discord.Embed(title='Message Delete', description=f'A message from {message.author.mention} was deleted.')
                delembed2.add_field(name='Deleted Message Error:', value=f'Message is too long!', inline=False)
                await channel.send(embed=delembed2)
                
#Bulk delete
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        channel = discord.utils.get(self.avimetry.get_all_channels(), name='bot-logs')
        purgeembed=discord.Embed(title='Message Purge', description=f'Bulk delete detected. Information is below.')
        purgeembed.add_field(name='Affected messages:', value=f"Channel: {messages.channel} \n Amount: {len(messages)} messages")
        await channel.send(embed=purgeembed)

#Toggle Command
    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx):
        a = discord.Embed()
        a.add_field(name="Options", value="chatlogs, botlogs")
        await ctx.send(embed=a)
    @logs.command()
    async def chatlogs(self, ctx, toggle : str):
        with open("./avimetrybot/files/bot-logs.json", "r") as f:
            msglogger = json.load(f)
        if toggle == "true":
            a = discord.Embed()
            a.add_field(name="Chat Logs", value="Chat Logs set to `true`")
            await ctx.send(embed=a)
            msglogger[str(ctx.guild.id)] = 1
            with open("./avimetrybot/files/bot-logs.json", "w") as f:
                json.dump(msglogger, f, indent=4)
        if toggle == "false":
            msglogger[str(ctx.guild.id)] = 0
            with open("./avimetrybot/files/bot-logs.json", "w") as f:
               json.dump(msglogger, f, indent=4)
            b = discord.Embed()
            b.add_field(name="Chat Logs", value="Chat Logs set to `true`")
            await ctx.send(embed = b)
    '''
def setup(avimetry):
    avimetry.add_cog(BotLogs(avimetry))