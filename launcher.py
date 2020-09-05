
import sys
import yaml
import logging
from argparse import ArgumentParser

from discord.ext import commands

from bot import Squire
from utils import checks
from authentication import TOKEN
from utils.utility import setup_logger, module_logger, HOME_DIR


def main():

    parser = ArgumentParser(description="Start the bot")
    parser.add_argument('--debug', '-d', action='store_true')

    args = parser.parse_args()
    debug = args.debug

    if sys.platform != 'linux' or debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    bot_logger = setup_logger(name)
    logger = module_logger(name, "launcher", level)
    module_logger(name, 'discord', logging.INFO)

    logger.info(f"Starting {name}.")

    bot = Squire()

    logger.info("Calling run method.")
    try:
        bot.run(TOKEN)
    finally:
        try:
            exit_code = bot._exit_code
        except AttributeError:
            logger.info("Bot's exit code could not be retrieved.")
            exit_code = 0
        logger.info(f"Bot closed with exit code {exit_code}.")
        exit(exit_code)

if __name__ == "__main__":
    main()
