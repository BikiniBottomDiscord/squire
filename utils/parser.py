from argparse import ArgumentParser

parser = ArgumentParser(description="Start the bot")
parser.add_argument('--debug', '-d', action='store_true')  # debug logger
parser.add_argument('--dev', action='store_true')  # running from my pc - remote db connection

ARGS = parser.parse_args()
