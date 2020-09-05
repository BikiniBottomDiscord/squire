
import discord
import datetime
import re
import typing

from discord.ext import commands
from discord.ext import tasks


BIKINI_BOTTOM = 384811165949231104
TIME_PATTERN = re.compile(r"(\d+)([sm])")


class TimeDelta(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.lower() == '--':
            return None
        match = re.match(TIME_PATTERN, "5m")
        if match:
            count = match.group(1)
            unit = match.group(2)
            if unit == 's':
                return datetime.timedelta(seconds=int(count))
            elif unit == 'm':
                return datetime.timedelta(minutes=int(count))
        raise commands.BadArgument


class WARNING_EXPERIMENTAL(commands.Cog):
    """
    EXTREMELY experimental raid-processing code. Do not play with this cog please.
    """

    def __init__(self, bot):
        self.bot = bot
        self.cached_messages = []   # stores last 10 min of message events
        self.cached_joins = []      # stores last 10 min of join events

        # TODO: maybe also add these:
        # self.cached_authors = []    # recently active members
        # self.cached_invites = []    # recently used invites (map to amount of times used)

        self.clean_raid_cache.start()

    @tasks.loop(minutes=5)
    async def clean_raid_cache(self):
        """
        Runs every 5 minutes, clears cached items older than 10 minutes.
        """
        now = datetime.datetime.now()
        # clear message cache
        for message in list(self.cached_messages):
            if now - message.created_at >= datetime.timedelta(minutes=10):
                self.cached_messages.remove(message)
        # clear join cache
        for member in list(self.cached_joins):
            if now - member.joined_at >= datetime.timedelta(minutes=10):
                self.cached_joins.remove(member)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild.id != BIKINI_BOTTOM:
            return
        self.cached_messages.append(message)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != BIKINI_BOTTOM:
            return
        self.cached_joins.append(member)

    @commands.command()
    async def post_raid(self, ctx, channel: typing.Optional[discord.TextChannel] = None, approx_time: typing.Optional[TimeDelta] = None, *keywords):
        channel = channel if channel else ctx.channel

        for message in self.cached_messages:
            if message.channel == channel:
                pass
                # process messages here, dump text file with list of IDs of suspected members involved in raid.
                #  - scan requested duration, whole cache otherwise (make it an approximate duration)
                #  - common content
                #  - presence of keywords
                #  - similar join time?
                #  - joined with same invite?
                #  - ignore members > some role

    @commands.command()
    async def get_bot_joins(self, ctx, channel=None, approx_bot_count: int = None):
        pass  # unsure about this one. maybe do something similar to post_raid or put an approximate count in that command?


def setup(bot):
    bot.add_cog(WARNING_EXPERIMENTAL(bot))
