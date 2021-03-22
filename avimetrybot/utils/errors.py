from discord.ext import commands


class TimeZoneError(commands.BadArgument):
    def __init__(self, argument):
        self.argument = argument
        super().__init__(
            'Timezone "{}" was not found. [Here](https://gist.github.com/Soheab/3bec6dd6c1e90962ef46b8545823820d) '
            'are all the valid timezones you can use.'.format(argument)
        )


class Blacklisted(commands.CheckFailure):
    def __init__(self, reason):
        self.reason = reason


class AvizumsLoungeOnly(commands.CheckFailure):
    pass
