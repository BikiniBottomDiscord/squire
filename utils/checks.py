import logging

from discord.ext import commands

from utils.settings import MODS, ADMINS


logger = logging.getLogger('utils.checks')


def is_admin(user):
    return user.id in ADMINS


def is_mod(user):
    return user.id in MODS


def hall_monitor():
    return commands.check(is_admin)


def lifeguard():
    return commands.check(is_mod)
