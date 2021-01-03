import os
import discord
import logging

from discord.ext import commands

from utils import settings
# from utils.checks import is_mod


logger = logging.getLogger('bot')


class Squire(commands.Bot):
    def __init__(self, started_at, **kwargs):
        super().__init__(
            command_prefix=settings.prefix,
            description="sQUIRE, Defender of Bikini Bottom",
            help_command=commands.MinimalHelpCommand(),
            intents=discord.Intents.all(),
            **kwargs
        )
        self.version = settings.version
        self.started_at = started_at
        # self.add_check(lambda ctx: is_mod(ctx.author))
        self._exit_code = 0

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}. Bot is ready.")

    async def on_message(self, message):
        # ignore bots
        if message.author.bot:
            return
        # process_commands
        else:
            await self.process_commands(message)

    def load_cogs(self):
        logger.info('Loading cogs.')
        cogs = ['jishaku'] + [f"cogs.{file[:-3]}" for file in os.listdir('./cogs') if file.endswith('.py')]
        for cog in cogs:
            try:
                self.load_extension(cog)
                logger.info(f' - {cog}')
            except commands.ExtensionFailed as e:
                logger.exception(f"Failed to load cog {cog} [{e.__class__.__name__}: {e}]")
        logger.info('Cogs loaded.')


