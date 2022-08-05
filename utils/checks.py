import logging

from disnake.ext import commands

from utils.settings import ADMINS, MODS

logger = logging.getLogger("utils.checks")


def _has_role(user, roleid):
    for role in user.roles:
        if role.id == roleid:
            return True
    return False


def is_admin(user):
    return user.id in ADMINS


def is_mod(user):
    return is_admin(user) or _has_role(user, 736363032304943135)


def hall_monitor():
    async def func(ctx):
        return is_admin(ctx.author)

    return commands.check(func)


def lifeguard():
    async def func(ctx):
        return is_mod(ctx.author)

    return commands.check(func)
