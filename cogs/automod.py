import discord
from discord.ext import commands
import random
import asyncio
import json
import datetime

class AutoMod(commands.Cog):
    
    def __init__(self, avibot):
        self.avibot = avibot
        self.mc = commands.CooldownMapping.from_cooldown(10, 10, commands.BucketType.member)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.avibot.user:
            return
        
        with open("files/badword.json", "r") as f:
            blacklist = json.load(f)

        for words in blacklist:
            if words in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention}, don't say that word!", delete_after=3)

        bucket = self.mc.get_bucket(message)
        ra = bucket.update_rate_limit()
        role = message.guild.get_role(761032535688871967)
        member = message.author
        if ra:
            with open("files/automod.json", "r") as f:
                offenses = json.load(f)
            if str(message.author.id) in offenses:
                if offenses[str(message.author.id)] == 1: 
                    offenses[str(message.author.id)] = 2 
                    await message.channel.send("Do not spam. You have been auto-muted for 4 minutes.")
                    with open("files/automod.json", "w") as f:
                        json.dump(offenses, f, indent=4)
                    await member.add_roles(role)
                    await asyncio.sleep(240)
                    await member.remove_roles(role)
                
                elif offenses[str(message.author.id)] == 2:
                    offenses[str(message.author.id)] = 3
                    await message.channel.send("Do not spam. You have been auto-muted for 8 minutes.")
                    with open("files/automod.json", "w") as f:
                        json.dump(offenses, f, indent=4)
                    await member.add_roles(role)
                    await asyncio.sleep(480)
                    await member.remove_roles(role)
                
                elif offenses[str(message.author.id)] == 3:
                    offenses[str(message.author.id)] = 4
                    await message.channel.send("Do not spam. You have been auto-muted for 16 minutes.")
                    with open("files/automod.json", "w") as f:
                        json.dump(offenses, f, indent=4)
                    await member.add_roles(role)
                    await asyncio.sleep(960)
                    await member.remove_roles(role)
                
                elif offenses[str(message.author.id)] == 4:
                    offenses[str(message.author.id)] = 5
                    await message.channel.send("Do not spam. You have been auto-muted for 32 minutes.")
                    with open("files/automod.json", "w") as f:
                        json.dump(offenses, f, indent=4)
                    await member.add_roles(role)
                    await asyncio.sleep(1960)
                    await member.remove_roles(role)
                
                elif offenses[str(message.author.id)] == 5:
                    offenses[str(message.author.id)] = 6
                    await message.channel.send("Do not spam. You have been auto-muted for 50 minutes. **This is your last warning before getting banned**.")
                    with open("files/automod.json", "w") as f:
                        json.dump(offenses, f, indent=4)
                    await member.add_roles(role)
                    await asyncio.sleep(3000)
                    await member.remove_roles(role)
                
                else:
                    try:
                        offenses[str(message.author.id)] = 1
                        bae=discord.Embed(title=f"You have been auto-banned from {member.guild.name}", timestamp=datetime.datetime.utcnow())
                        bae.add_field(name= "Moderator:", value=f"None \n`None`")
                        bae.add_field(name="Reason:", value="Anti-Spam")
                        await member.send(embed=bae)
                        await member.ban(reason="Anti-Spam")
                        banembed=discord.Embed()
                        banembed.add_field(name="<:aviSuccess:777096731438874634> Auto-Banned Member", value=f"{member.mention} (`{member.id}`) has been auto-banned from **{message.guild.name}**.", inline=False)
                        await message.channel.send(embed=banembed)
                        with open("files/automod.json", "w") as f:
                            json.dump(offenses, f, indent=4)
                    except discord.Forbidden:
                        print("Forbidden")
                    
                
            else:
                with open("files/automod.json", "r") as f:
                    offenses = json.load(f)
                offenses[str(message.author.id)] = 1
                
                print("offence1")
                await message.channel.send("Do not spam. You have been auto-muted for 2 minutes ") 
                with open("files/automod.json", "w") as f:
                    json.dump(offenses, f, indent=4)

        else:
            return

    

def setup(avibot):
    avibot.add_cog(AutoMod(avibot))


