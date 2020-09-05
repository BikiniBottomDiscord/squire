import discord
from discord.ext import commands

import io
import asyncio
import subprocess
import traceback
import textwrap
import contextlib
import datetime
import random

from authentication import TOKEN




class Squire(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.description = "sQUIRE, Rev's eval bot"
        self.load_extension('jishaku')
        self.load_extension('cogs.modlog')
        self.load_extension('cogs.admin')
        self.started_at = datetime.datetime.now()
        self.add_check(lambda ctx: check(ctx.author))
        self.help_command = commands.MinimalHelpCommand()

    async def on_ready(self):
        print(f"Logged in as {self.user}.")

    async def ping_response(self, channel):
        await channel.send(embed=discord.Embed(title=f"sQUIRE ({datetime.datetime.now() - self.started_at})",
                                               description=f"Prefix: `{self.command_prefix}`"))

    async def on_message(self, message):
        # ignore bots
        if message.author.bot:
            return
        # if I ping it
        elif check(message.author) and message.content in [f'<@!{self.user.id}>', f'<@{self.user.id}>']:
            await self.ping_response(message.channel)
        # process_commands
        else:
            await self.process_commands(message)