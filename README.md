# Alpine

[![Discord Server](https://discord.com/api/guilds/751490725555994716/embed.png)](https://discord.gg/hWhGQ4QHE9)

[![Discord Bots](https://top.gg/api/widget/756257170521063444.svg)](https://top.gg/bot/756257170521063444)

[Project Page](https://avizum.dev/projects/alpine)

A bot written in Python by [avizum (Discord)](https://discord.com/users/750135653638865017)

### Bot Invite
You can add Alpine to your server with [this link](https://discord.com/oauth2/authorize?client_id=756257170521063444&scope=bot&permissions=2147483647). Thanks!


## Running the bot
I request that you do not run your own instance of Alpine. Please use the one that I run.
You can add Alpine to your server with the link above.

If for some reason, you still want to run your own instance, here are some instructions:

### Prerequisites
- This project uses [uv](https://docs.astral.sh/uv/#installation) for dependency management. Install uv first.
- Alpine is deployed on Ubuntu, for best results, use a Linux-based distro
- [Lavalink](https://lavalink.dev/) is used for the music system. If you want music to work, install it first.
- Install [PostgreSQL](https://www.postgresql.org/).

1. Clone the Repository
`git` clone the repository:
```sh
git clone https://github.com/avizum/alpine
```

2. Install Project Dependencies
After cloning, install the dependencies with `uv`
```sh
uv sync
```

3. Configure the Bot
- Create a `config.toml` and place all your tokens in there. For an example, check `config_example.toml`.
- In `core/alpine.py`:
    - Set the `OWNER_IDS` variable to your Discord user ID(s)
    - Set the `PUBLIC_BOT_ID` to your Bot's (App) user ID.
- Configure the PostgreSQL databse

4. Run the Bot
To run the bot, run
```sh
uv run main.py
```

<sup>Copyright (C) 2021-present  avizum</sup>
