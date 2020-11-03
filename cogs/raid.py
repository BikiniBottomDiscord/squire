
import discord
import datetime
import re
import typing
import asyncio
import logging

from discord.ext import commands
from discord.ext import tasks


logger = logging.getLogger('cogs.raid')


BIKINI_BOTTOM = 384811165949231104
TEXT_CHANNELS_CATEGORY = 384811165949231105
ADMINISTRATIVE_CATEGORY = 384814507849023509

TIME_PATTERN = re.compile(r"(\d+)([sm])")
ROLES = [
    476850644456833024,  # bikini bottomite
    481686386060034048,  # announcement interest
    480870762153115649,  # lets watch
    586266611233849348,  # minecraft
    537004601753337878,  # jelly spotter
    740028577189331025,  # affiliate
    653494481622007828,  # giveaway
    740457132662718524,  # game night
    541810707386335234,  # bad noodle
    681916546951806983,  # bad-ish noodle
]
BAD_NOODLE = 541810707386335234

CACHE_REMOVE_AGE_THRESHOLD = 10  # minutes


class TimeDelta(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.lower() == '--':
            return None
        match = re.match(TIME_PATTERN, argument)
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
        self.cached_invites = {}    # recently used invites (map to amount of times used)

        # TODO: maybe also add:
        # self.cached_authors = []    # recently active members

        self.last_invite_state = {}
        self.last_cache_update = None

        self.clean_raid_cache.start()

    @tasks.loop(minutes=5)
    async def clean_raid_cache(self):
        """
        Runs every 5 minutes, clears cached items older than 10 minutes.
        """
        now = datetime.datetime.now()
        age_threshold = datetime.timedelta(minutes=CACHE_REMOVE_AGE_THRESHOLD)
        self.last_cache_update = now

        # clear message cache
        for message in list(self.cached_messages):
            if now - message.created_at >= age_threshold:
                self.cached_messages.remove(message)

        # clear join cache
        for member in list(self.cached_joins):
            if now - member.joined_at >= age_threshold:
                self.cached_joins.remove(member)

        # clear invite cache
        for code, join_list in list(self.cached_invites.items()):
            for timestamp in list(join_list):
                if now - timestamp >= age_threshold:
                    join_list.remove(timestamp)
            if len(join_list) == 0:
                self.cached_invites.pop(code)

    @commands.Cog.listener()
    async def on_ready(self):
        # setup invite state (for invite tracking)
        guild = self.bot.get_guild(BIKINI_BOTTOM)
        self.last_invite_state = dict([(invite.code, invite.uses) for invite in await guild.invites()])

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild.id != BIKINI_BOTTOM:
            return
        self.cached_messages.append(message)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != BIKINI_BOTTOM:
            return

        # update join cache
        self.cached_joins.append(member)

        await asyncio.sleep(2)

        if not self.last_invite_state:
            self.last_invite_state = dict([(invite.code, invite.uses) for invite in await member.guild.invites()])
            return

        # update invite cache
        new_invite_state = dict([(invite.code, invite.uses) for invite in await member.guild.invites()])
        for code, uses in new_invite_state.items():
            old_uses = self.last_invite_state.get(code, 0)
            if old_uses < uses:
                if code not in self.cached_invites.keys():
                    self.cached_invites[code] = []
                for i in range(uses - old_uses):
                    self.cached_invites[code].append(datetime.datetime.now())

        self.last_invite_state = new_invite_state


    @commands.command()
    async def dump_cache_size(self, ctx):
        await ctx.send(f"__RAID CACHE:__\n"
                       f"> cached_messages: {len(self.cached_messages)}\n"
                       f"> cached_joins: {len(self.cached_joins)}\n"
                       f"> cached_invites: {len(self.cached_invites)}\n"
                       f"cache last updated {self.last_cache_update}"
                       )

    @commands.command()
    async def post_raid(self, ctx, channel: typing.Optional[discord.TextChannel] = None, approx_time: typing.Optional[TimeDelta] = None, *keywords):
        """INCOMPLETE"""
        return await ctx.send("This command is not ready yet.")
        channel = channel if channel else ctx.channel
        now = datetime.datetime.now()
        flagged_members = set()
        ignored_members = set()
        flagged_messages = []

        for message in self.cached_messages:
            if message.channel == channel:
                if approx_time and (now - message.created_at) > approx_time:  # ignore messages
                    continue
                if message.author in ignored_members:  # members who are safe
                    continue
                if [role for role in message.author.roles if role.id not in ROLES]:  # if they have any roles not in this list, they're safe.
                    ignored_members.add(message.author)
                    continue


                # process messages here, dump text file with list of IDs of suspected members involved in raid.
                #  - scan requested duration, whole cache otherwise (make it an approximate duration)
                #  - common content
                #  - presence of keywords
                #  - similar join time?
                #  - joined with same invite?
                #  - ignore members > some role


    @commands.command()
    async def get_bot_joins(self, ctx, channel=None, approx_bot_count: int = None):
        """INCOMPLETE"""
        return await ctx.send("This command is not ready yet.")  # unsure about this one. maybe do something similar to post_raid or put an approximate count in that command?


    @commands.command()
    async def count_suspicious_joins(self, ctx):
        now = datetime.datetime.now()
        join_count = len(self.cached_joins)
        invite_count = len(self.cached_invites)
        analysis = f"`{join_count}` members joined recently, using `{invite_count}` invites.\n"

        guild_invites = await ctx.guild.invites()

        for code, join_list in self.cached_invites.items():
            joins = len(join_list)
            for invite in guild_invites:
                if invite.code == code:
                    inviter = invite.inviter
                    uses = invite.uses
                    if joins > 1 and joins >= (join_count / 2):
                        analysis += f"`{joins}` members joined using invite `{code}` (created by {inviter.mention}, `{uses}` total uses)\n"
                    if joins > 1 and (now - invite.created_at) <= datetime.timedelta(minutes=30):
                        analysis += f"Invite `{code}` was created about `{round((now - invite.created_at).seconds / 60)}` minutes ago and used {uses} times\n"
                    if isinstance(inviter, discord.Member):
                        if (invite.created_at - inviter.joined_at) <= datetime.timedelta(minutes=30) and (now - inviter.joined_at) <= datetime.timedelta(minutes=60):
                            analysis += f"New user {inviter.mention} created invite `{code}` about `{round((invite.created_at - inviter.joined_at).seconds / 60)}` minutes after joining\n"

                    max_joins_within_duration_limit = 0
                    duration_limit = datetime.timedelta(minutes=5)
                    duration_range = None
                    for a, first_timestamp in enumerate(join_list):
                        for b, last_timestamp in enumerate(join_list):
                            if a >= b or (duration_range and a >= duration_range[0] and b <= duration_range[1]):
                                continue
                            if last_timestamp - first_timestamp < duration_limit:
                                count = b - a + 1  # it's an inclusive range
                                if count > max_joins_within_duration_limit:
                                    max_joins_within_duration_limit = count
                                    duration_range = (a, b)
                    if max_joins_within_duration_limit:
                        duration = join_list[duration_range[1]] - join_list[duration_range[0]]
                        minutes = round(duration.seconds / 60)
                        if max_joins_within_duration_limit > minutes:
                            analysis += f"`{max_joins_within_duration_limit}` members joined using invite `{code}` in `{minutes}` minutes"

        recently_created = 0
        for member in self.cached_joins:
            if (member.joined_at - member.created_at) < datetime.timedelta(minutes=60):
                recently_created += 1
        if recently_created:
            analysis += f"`{recently_created}` new members joined within 1 hour of account creation\n"

        await ctx.send(analysis)


def setup(bot):
    bot.add_cog(WARNING_EXPERIMENTAL(bot))
