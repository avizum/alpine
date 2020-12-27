import discord
from discord.ext import commands
import random
import datetime
import json

class BotLogs(commands.Cog):

    def __init__(self, avibot):
        self.avibot = avibot

#Message Logger
    @commands.Cog.listener()
    async def on_message(self, message):
        with open("files/prefixes.json", "r") as f:
                prefixes = json.load(f)
        if message.guild is None:
            return
        global pre
        pre = prefixes[str(message.guild.id)]
        if message.author == self.avibot.user:
            return
        elif message.author.bot:
            return
        elif message.channel == discord.utils.get(self.avibot.get_all_channels(), name='secret-chat'):
            return
        elif message.channel == discord.utils.get(self.avibot.get_all_channels(), name='verify'):
            return
        elif message.content.startswith(pre):
            return
        elif message.attachments:
            channel = discord.utils.get(self.avibot.get_all_channels(),  name='chat-logs')
            mcontent=message.attachments[0].url
            embed=discord.Embed(title=f"Image from {message.author}, Server {message.guild}", timestamp=datetime.datetime.utcnow())
            embed.set_image(url=f'{mcontent}')
            await channel.send(embed=embed)
        elif message.content:
            channel = discord.utils.get(self.avibot.get_all_channels(),  name='chat-logs')
            mcontent=message.content
            embed=discord.Embed(title=f"Message from {message.author}, Server {message.guild}", description=f"`{mcontent}`",timestamp=datetime.datetime.utcnow())
            await channel.send(embed=embed) 

#Message Edit
    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        channel = discord.utils.get(self.avibot.get_all_channels(), name='bot-logs')
        if message_before.author == self.avibot.user:
            return
        elif message_before.content.startswith(pre):
            return
        elif message_after.content.startswith(pre):
            return
        elif message_before.channel == discord.utils.get(self.avibot.get_all_channels(), name='verify'):
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
        channel = discord.utils.get(self.avibot.get_all_channels(), name='bot-logs')
        if message.channel == discord.utils.get(self.avibot.get_all_channels(), name='verify'):
            return
        elif message.author.bot:
            return
        elif message.author == self.avibot.user:
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
        channel = discord.utils.get(self.avibot.get_all_channels(), name='bot-logs')
        purgeembed=discord.Embed(title='Message Purge', description=f'Bulk delete detected. Information is below.')
        purgeembed.add_field(name='Affected messages:', value="{} messages".format(len(messages)))
        await channel.send(embed=purgeembed)


def setup(avibot):
    avibot.add_cog(BotLogs(avibot))