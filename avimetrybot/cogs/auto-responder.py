import discord
from discord.ext import commands
import random
import time
import asyncio
import json

class AutoResponder(commands.Cog):

    def __init__(self, avibot):
        self.avibot = avibot

    #If Bot is pinged it responds with prefix
    @commands.Cog.listener()
    async def on_message(self, message):
        

        with open("./avimetrybot/files/counting.json", "r") as f:
            cc = json.load(f)
            if str(message.guild.id) in cc:
                if message.channel.name == "counting":
                    if message.author.bot:
                        await message.delete()
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

        if message.author == self.avibot.user:
            return
           
        if message.content == '<@!756257170521063444>':
            with open("./avimetrybot/files/prefixes.json", "r") as f:
                prefixes = json.load(f)
            pre = prefixes[str(message.guild.id)]
            await message.channel.send(f"Hey, {message.author.mention}, my prefix is `{pre}`")
         

            if message.content !=str(cc):
                await message.delete()
            else:
                with open("./avimetrybot/files/counting.json", "r") as f:
                    cc = json.load(f)
                
                cc[str(message.guild.id)] = 2
                with open("./avimetrybot/files/counting.json", "w") as f:
                    json.dump(cc, f, indent=4)
            
def setup(avibot):
    avibot.add_cog(AutoResponder(avibot))
