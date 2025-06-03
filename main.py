"""
Runs the bot.
Copyright (C) 2021 - 2024 avizum

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse

from core import alpine, Bot

parser = argparse.ArgumentParser("Alpine Bot")
parser.add_argument("-b", "--beta", action="store_true")
parsed = parser.parse_args()


def main():
    bot = Bot()
    tokens = bot.settings["bot_tokens"]

    if parsed.beta:
        bot.token = tokens["AlpineII"]
        alpine.BOT_ID = alpine.BETA_BOT_ID

    bot.token = tokens["Alpine"] if not parsed.beta else tokens["AlpineII"]
    bot.run()


if __name__ == "__main__":
    main()
