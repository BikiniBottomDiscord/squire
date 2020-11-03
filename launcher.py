
import sys
import datetime
import logging
from argparse import ArgumentParser

from bot import Squire
from utils import checks
from authentication import TOKEN
from utils.utility import setup_logger


logger = logging.getLogger('launcher')

started_at = datetime.datetime.now()


def main():

    parser = ArgumentParser(description="Start the bot")
    parser.add_argument('--debug', '-d', action='store_true')

    args = parser.parse_args()
    debug = args.debug

    setup_logger('discord', False, started_at)
    setup_logger('launcher', debug, started_at)
    setup_logger('bot', debug, started_at)
    setup_logger('cogs', debug, started_at)
    setup_logger('utils', debug, started_at)

    logger.info(f"Initializing bot.")
    bot = Squire()

    logger.info("Loading cogs.")
    bot.load_cogs()

    logger.info("Starting bot.")
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
