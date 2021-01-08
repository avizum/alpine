import discord
from discord.ext import commands
import random
import time
import asyncio
import json

class Counting(commands.Cog):

    def __init__(self, avimetry):
        self.avimetry = avimetry

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avimetry.user:
            return
        if message.guild is None:
            return
        with open("./avimetrybot/files/counting.json", "r") as f:
            cc = json.load(f)
            if str(message.guild.id) in cc:
                if message.channel.name == "counting":
                    if message.author.bot:
                        await message.delete()
                    elif message.author == self.avimetry.user:
                        return
                    elif message.content != str(cc[str(message.guild.id)]):
                        await message.delete()
                    else:
                        with open("./avimetrybot/files/counting.json", "r") as f:
                            cc = json.load(f)
                    
                        cc[str(message.guild.id)] +=1
                        with open("./avimetrybot/files/counting.json", "w") as f:
                            json.dump(cc, f, indent=4)
            else:
                cc[str(message.guild.id)] = 0
                with open("./avimetrybot/files/counting.json", "w") as f:
                    json.dump(cc, f, indent=4)
    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        if message_after.author == self.avimetry.user:
            return
        if message_after.channel.name == "counting":
            await message_after.delete()
            await message_after.channel.send("Don't Edit Messages", delete_after=5)
            with open("./avimetrybot/files/counting.json", "r") as f:
                cc = json.load(f)
                        
            cc[str(message_after.guild.id)] -=1
            with open("./avimetrybot/files/counting.json", "w") as f:
                json.dump(cc, f, indent=4)         

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setcount(self, ctx, count : int):
        with open("./avimetrybot/files/counting.json", "r") as f:
            cc = json.load(f)
                        
        cc[str(ctx.guild.id)] = count
        with open("./avimetrybot/files/counting.json", "w") as f:
            json.dump(cc, f, indent=4)         



def setup(avimetry):
    avimetry.add_cog(Counting(avimetry))
