import logging

from discord.ext import commands

from utils.settings import ADMINS, MODS

logger = logging.getLogger("utils.checks")


def is_admin(user):
    return user.id in ADMINS


def is_mod(user):
    return user.id in MODS


def hall_monitor():
    async def func(ctx):
        return is_admin(ctx.author)

    return commands.check(func)


def lifeguard():
    async def func(ctx):
        return is_mod(ctx.author)

    return commands.check(func)
