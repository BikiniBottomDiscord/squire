import datetime
import logging
from os import environ

from bot import Squire
from utils.parser import ARGS
from utils.utility import setup_logger

logger = logging.getLogger("launcher")
started_at = datetime.datetime.now()

# TOKEN = environ.get("TOKEN")
from auth import TOKEN


def main():

    debug = ARGS.debug

    setup_logger("discord", False, started_at)
    setup_logger("launcher", debug, started_at)
    setup_logger("bot", debug, started_at)
    setup_logger("cogs", debug, started_at)
    setup_logger("utils", debug, started_at)

    logger.info(f"Initializing bot.")
    bot = Squire(started_at)

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
