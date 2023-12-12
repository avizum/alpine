# Alpine

[![Discord Server](https://discord.com/api/guilds/751490725555994716/embed.png)](https://discord.gg/muTVFgDvKf)

[![Discord Bots](https://top.gg/api/widget/756257170521063444.svg)](https://top.gg/bot/756257170521063444)


A bot written in Python by [avizum](https://discord.com/users/750135653638865017)

### Bot Invite
Invite Alpine [here](https://discord.com/oauth2/authorize?client_id=756257170521063444&scope=bot&permissions=2147483647)


#### Commands to get you started
|           Command          |            Description            |
|:--------------------------:|:---------------------------------:|
| `a.help [command\|module]` |      Shows the bot help menu      |
|   `a.prefix add <prefix>`  |    Adds a prefix to your server   |
| `a.prefix remove <prefix>` | Removes a prefix from your server |
|          `a.about`         |    Shows the bot's information    |


#### Help Command
In the help command, you can see all the commands. If you need help reading the command signature, here they are.

|    Signature   |       Meaning      |
|:--------------:|:------------------:|
|  \<argument\>  |  required argument |
|   [argument]   | optional arguments |
| [arguments...] | multiple arguments |

## Running the bot
It is not recommended to run your own instance. Use the one [here.](https://discord.com/oauth2/authorize?client_id=756257170521063444&scope=bot&permissions=2147483647)

If you don't care, Here are instructions on how to run your own version of Alpine.

1. Have Python 3.10 installed

Python has to be installed. This is a Python bot.

2. Install requirements

Run `pip install -U -r requirements.txt`

3. Bot Configuration

Put your tokens in a `config.toml` file. Check `config_example.toml` for an example.
In `core/alpine.py`, change `OWNER_IDS` to your Discord IDs and change `PUBLIC_BOT_ID` to your bot's ID.
Set your PostgreSQL database (Will add more instructions soon)
Run main file.
