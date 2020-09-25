import discord
import subprocess
import textwrap
import traceback
import random
import asyncio
import io
import logging
import contextlib

from discord.ext import commands


logger = logging.getLogger('cogs.admin')


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None

    @staticmethod
    def cleanup_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    async def run_process(self, command):
        try:
            process = await asyncio.create_subprocess_shell(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await process.communicate()
        except NotImplementedError:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = await self.bot.loop.run_in_executor(None, process.communicate)

        return [output.decode() for output in result]

    @commands.command()
    async def test(self, ctx):
        if random.randint(0, 1) == 1:
            await ctx.guild.me.edit(nick="Ol' Reliable")
            await ctx.send("Whoosh whoosh, on GCP! <:bluejellyfish:479723952265232396> v1.1.0")
        else:
            await ctx.guild.me.edit(nick="Jellyfish")
            await ctx.send("Buzz Buzz, on GCP! <:jellyfish:479723952890052608> v1.1.0")
        await ctx.guild.me.edit(nick=None)

    @commands.command(name='eval', aliases=['e'])
    async def _eval(self, ctx, *, body: str):
        """Runs arbitrary python code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_ret': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with contextlib.redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            # try:
            #     await ctx.message.add_reaction('ðŸ˜Ž')
            # except:
            #     pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command()
    async def membercount(self, ctx):
        await ctx.send(len(await ctx.guild.fetch_members().flatten()))

    @commands.command()
    async def joinpos(self, ctx, member: discord.Member = None):
        member = member if member else ctx.author
        order = sorted((await ctx.guild.fetch_members().flatten()), key=lambda m: m.joined_at)
        join_pos = order.index(member) + 1
        await ctx.send(join_pos)
