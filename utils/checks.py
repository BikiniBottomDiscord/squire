import logging

from discord.ext import commands

logger = logging.getLogger('utils.checks')


def is_admin(user):
    return user.id in {
        204414611578028034,  # rev
        304695409031512064,  # dove
        426550338141683713,  # dee
        224323277370294275,  # kiwi
        298497141490450432,  # swine
    }


def is_mod(user):
    return user.id in {
        204414611578028034,  # nwunder#0003
        279722793891790848,  # Moistley#5939
        533087803261714433,  # Neptune's Helper#0039
        375375057138089986,  # Saturnfive050#1337
        304695409031512064,  # dovedevic#0522
        280874216310439938,  # egg#2222
        448250281097035777,  # No Jons#1299
        224323277370294275,  # Kiwi#6666
        299023554127593473,  # mzone#1771
        298497141490450432,  # AdventurousSwine#9894
    }


def hall_monitor():
    return commands.check(is_admin)


def lifeguard():
    return commands.check(is_mod)