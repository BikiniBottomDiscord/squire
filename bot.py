import os
import discord
import datetime
import logging

from discord.ext import commands

from launcher import started_at


logger = logging.getLogger('bot')


def check(user):
    return user.id in {
        204414611578028034,  # rev
        304695409031512064,  # dove
        426550338141683713,  # dee
        224323277370294275,  # kiwi
        298497141490450432,  # swine
        448250281097035777,  # nojons
    }


class Squire(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.description = "sQUIRE, Defender of Bikini Bottom"
        self.load_extension('jishaku')
        self.load_extension('modlog')
        self.started_at = started_at
        self.add_check(lambda ctx: check(ctx.author))
        self.help_command = commands.MinimalHelpCommand()
        self._exit_code = 0

    async def on_ready(self):
        print(f"Logged in as {self.user}.")

    async def on_message(self, message):
        # ignore bots
        if message.author.bot:
            return
        # process_commands
        else:
            await self.process_commands(message)

    def load_cogs(self):
        logger.info('Loading cogs.')
        cogs = ['jishaku'] + [f"cogs.{file}" for file in os.listdir('./cogs') if file.endswith('.py')]
        for cog in cogs:
            try:
                self.load_extension(cog)
                logger.info(f' - {cog}')
            except commands.ExtensionFailed as e:
                logger.exception(f"Failed to load cog {cog}")
        logger.info('Cogs loaded.')


