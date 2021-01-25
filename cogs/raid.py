import aiohttp
import asyncio
import datetime
import discord
import logging
import re
import io

from discord.ext import commands
from discord.ext import tasks
from typing import Union

from utils.checks import is_mod, is_admin
from utils.converters import FetchedUser
from utils.argparse_but_better import ArgumentParser

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

CACHE_REMOVE_AGE_THRESHOLD = 20  # minutes


async def confirm_action(ctx, prompt):
    m = await ctx.send(prompt)

    def check(_msg):
        return _msg.author == ctx.author

    message = await ctx.bot.wait_for('message', check=check)
    return message.content.lower() in ['y', 'yes']


class TimeDelta(commands.Converter):
    def convert_to_time(self, argument):
        match = re.match(TIME_PATTERN, argument)
        if match:
            count = match.group(1)
            unit = match.group(2)
            if unit == 's':
                return datetime.timedelta(seconds=int(count))
            elif unit == 'm':
                return datetime.timedelta(minutes=int(count))
        raise commands.BadArgument

    async def convert(self, ctx, argument):
        return self.convert_to_time(argument)


class WARNING_EXPERIMENTAL(commands.Cog):
    """EXTREMELY experimental raid-processing code. Do not play with this cog please."""

    def __init__(self, bot):
        self.bot = bot
        self.cached_messages = []   # stores last 10 min of message events
        self.cached_joins = []      # stores last 10 min of join events
        self.cached_invites = {}    # recently used invites (map to amount of times used)

        # TODO: maybe also add:
        # self.cached_authors = []    # recently active members

        self.last_invite_state = {}
        self.last_cache_update = None

        self.clean_raid_cache_task.start()

    def cog_check(self, ctx):
        return is_admin(ctx.author)

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

    @tasks.loop(minutes=5)
    async def clean_raid_cache_task(self):
        """Runs every 5 minutes, clears cached items older than 10 minutes."""
        age_threshold = datetime.timedelta(minutes=CACHE_REMOVE_AGE_THRESHOLD)
        await self.clean_raid_cache(age_threshold)

    async def clean_raid_cache(self, age_threshold):
        now = datetime.datetime.now()
        self.last_cache_update = now
        n = 0

        # clear message cache
        for message in list(self.cached_messages):
            if now - message.created_at >= age_threshold:
                self.cached_messages.remove(message)
                n += 1

        # clear join cache
        for member in list(self.cached_joins):
            if now - member.joined_at >= age_threshold:
                self.cached_joins.remove(member)
                n += 1

        # clear invite cache
        for code, join_list in list(self.cached_invites.items()):
            for timestamp in list(join_list):
                if now - timestamp >= age_threshold:
                    join_list.remove(timestamp)
                    n += 1
            if len(join_list) == 0:
                self.cached_invites.pop(code)

        return n

    @commands.group(name='raid', invoke_without_command=True)
    async def raid(self, ctx):
        await ctx.send_help(self.raid)

    @raid.group(name='cache', invoke_without_command=True)
    async def raid_cache(self, ctx):
        """Display the contents of sQUIRE's raid cache."""
        await ctx.send(
            f"__Raid Cache:__\n"
            f"> cached_messages: {len(self.cached_messages)}\n"
            f"> cached_joins: {len(self.cached_joins)}\n"
            f"> cached_invites: {len(self.cached_invites)}\n"
            f"cache last updated {self.last_cache_update}"
        )

    @raid_cache.command(name='clear')
    async def raid_cache_clear(self, ctx, age_limit: TimeDelta):
        """Clear messages and invites older than age_limit from cache."""
        await confirm_action(ctx, f"Are you sure you would like to clear items older than {age_limit}?")
        n = await self.clean_raid_cache(age_limit)
        await ctx.send(f"Cleared {n} items.")

    @raid.command(name='check')
    async def raid_check_invites(self, ctx):
        """Run some diagnostics on recent joins and return any notable information."""
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

    async def execute_raid_cleanup(
            self, ctx: commands.Context,
            channel: discord.TextChannel,
            approx_msg_time: datetime.timedelta = None,
            approx_join_time: datetime.timedelta = None,
            user_count: int = None,
            msg_content: str = None,
            mention_count_threshold: int = None,
            msg_contains_invite: bool = False,
            clean_at_end: bool = False,
            ban_at_end: bool = False
    ):
        """Runs an analysis on message cache and returns a list of flagged users."""

        await ctx.send(
            f"Executing post-raid cleanup with args ```\n(\n"
            f"    channel={str(channel)}\n"
            f"    {approx_msg_time=}\n"
            f"    {approx_join_time=}\n"
            f"    {user_count=}\n"
            f"    {msg_content=}\n"
            f"    {mention_count_threshold=}\n"
            f"    {msg_contains_invite=}\n"
            f"    {clean_at_end=}\n"
            f"    {ban_at_end=}\n"
            f")\n```"
        )

        now = datetime.datetime.now()

        flagged_members = set()
        ignored_members = set()
        flagged_messages = set()

        invite_regex = re.compile(r"(?:https?://)?discord.(?:com/invite|gg)/\w+")

        for message in self.cached_messages.copy():
            if not channel or message.channel == channel:

                logger.debug(f"checking message {message.id} by user {message.author.id}")

                # check reasons to ignore a user/message
                if message.author.id in ignored_members:  # members who are safe
                    logger.debug("  member in ignored_members")
                    continue
                if any((role.id not in ROLES) for role in message.author.roles):  # if they have any roles not in this list, they're safe.
                    logger.debug("  member has roles not in ROLES")
                    ignored_members.add(message.author.id)
                    continue
                if approx_join_time and (now - message.author.joined_at) > approx_join_time:  # ignore old users
                    logger.debug("  member is ignored due to account age")
                    ignored_members.add(message.author)
                    continue
                if approx_msg_time and (now - message.created_at) > approx_msg_time:  # ignore old messages
                    logger.debug("  message is ignored due to message age")
                    continue

                # check message against flag criteria
                logger.debug("  checking message against flag criteria")
                if mention_count_threshold:
                    if len(message.mentions) >= mention_count_threshold:
                        logger.debug("    message flagged by mention_count_threshold")
                        flagged_messages.add(message)
                        flagged_members.add(message.author.id)
                        continue
                if msg_contains_invite:
                    if invite_regex.search(message.content.lower()):
                        logger.debug("    message flagged by msg_contains_invite")
                        flagged_messages.add(message)
                        flagged_members.add(message.author.id)
                        continue
                if msg_content:
                    if msg_content in message.content.lower():
                        logger.debug("    message flagged by msg_content")
                        flagged_messages.add(message)
                        flagged_members.add(message.author.id)
                        continue

                # process messages here, dump text file with list of IDs of suspected members involved in raid.
                #  - scan requested duration, whole cache otherwise (make it an approximate duration)
                #  - common content
                #  - presence of keywords
                #  - similar join time?
                #  - joined with same invite?
                #  - ignore members > some role

        text = "\n".join([str(i) for i in flagged_members])
        fp = io.StringIO(text)
        await ctx.send(f"Flagged {len(flagged_members)} users.", file=discord.File(fp, "FLAGGED_USERS.txt"))

        if clean_at_end:
            # TODO
            await ctx.send("Message cleaning is currently not implemented.")

        if ban_at_end:
            # TODO
            await ctx.send("Mass banning is currently not implemented.")
            # await self.execute_massban(ctx, flagged_members)

    @raid.group(name='cleanup', invoke_without_command=True)
    async def raid_cleanup(self, ctx, *cmd_args):
        """Run a post-raid analysis, generating a list of user IDs. Outputs to a text file.

        Argument options:
        --channel CHANNEL
            The channel to check messages from. Defaults to current channel. '.' is shorthand for current channel, '*' is shorthand for "any channel".
        --time TIME
            Maximum message age. This will ignore messages older than the duration requested.
        --count COUNT
            Estimated user count. Currently does not affect this command's behavior.
        --content CONTENT
            Flag messages containing a particular substring.
        --mentions MENTIONS
            Flag messages containing MENTIONS or more mentions.
        --invite
            Bool, indicates that messages matching discord invite regex should be flagged.
        --clean
            Bool, indicates that flagged messages should be bulk deleted.
        --ban
            Bool, indicates that flagged users should be mass banned.
        """
        parser = ArgumentParser()
        parser.add_argument('--channel')
        parser.add_argument('--time', type=TimeDelta().convert_to_time)
        parser.add_argument('--count', type=int)
        parser.add_argument('--content')
        parser.add_argument('--mentions', type=int)
        parser.add_argument('--invite', action='store_true')
        # parser.add_argument('--regex', type=lambda arg: re.compile(arg.strip('`')))
        parser.add_argument('--clean', action='store_true')
        parser.add_argument('--ban', action='store_true')
        args = parser.parse_args(cmd_args)

        if args.channel:
            if args.channel == ".":
                channel = ctx.channel
            elif args.channel == "*":
                channel = None
            else:
                try:
                    channel = await commands.TextChannelConverter().convert(ctx, args.channel or "")
                except discord.DiscordException as e:
                    return await ctx.send(f"{e.__class__.__name__}: {e}")
        else:
            channel = ctx.channel

        await self.execute_raid_cleanup(
            ctx=ctx,
            channel=channel,
            approx_msg_time=args.time,
            approx_join_time=None,
            user_count=args.count,
            msg_content=args.content,
            mention_count_threshold=args.mentions,
            msg_contains_invite=args.invite,
            clean_at_end=args.clean,
            ban_at_end=args.ban,
        )

    @raid_cleanup.command()
    async def raid_cleanup_content(self, ctx, channel: discord.TextChannel, content: str, clean: bool = False):
        """Shortcut to process a channel based on a message's content."""
        if content.strip() == "":
            return await ctx.send("Content cannot be blank! Remember to provide a channel and message content.")
        await self.execute_raid_cleanup(
            ctx=ctx,
            channel=channel,
            approx_msg_time=None,
            approx_join_time=None,
            user_count=None,
            msg_content=content,
            mention_count_threshold=None,
            msg_contains_invite=False,
            clean_at_end=clean,
            ban_at_end=False
        )

    @raid_cleanup.command()
    async def raid_cleanup_mentions(self, ctx, channel: discord.TextChannel, mentions: int = 15, clean: bool = False):
        """Shortcut to process a channel based on a message's mention count. Mention count threshold defaults to 15."""
        await self.execute_raid_cleanup(
            ctx=ctx,
            channel=channel,
            approx_msg_time=None,
            approx_join_time=None,
            user_count=None,
            msg_content=None,
            mention_count_threshold=mentions,
            msg_contains_invite=False,
            clean_at_end=clean,
            ban_at_end=False
        )

    async def execute_massban(self, ctx, users):
        confirmation = await confirm_action(ctx, f"Are you sure you would like to ban {len(users)} users?")

        if confirmation:
            await ctx.send("Banning...")
            success = 0
            failed = 0
            for user in users:
                if isinstance(user, str):
                    user = int(user)
                if isinstance(user, int):
                    user = discord.Object(user)
                try:
                    await ctx.guild.ban(user, reason=f'Mass ban by {ctx.author}')
                    success += 1
                except discord.DiscordException:
                    failed += 1
            await ctx.send(f"Done. {success} successes, {failed} failures.")

        else:
            await ctx.send("Cancelled!")

    @commands.group(invoke_without_command=True)
    async def mban(self, ctx, *users: Union[discord.Member, discord.User, int]):
        """Bans a list of users"""
        await self.execute_massban(ctx, users)

    @mban.command(name='file')
    async def mban_file(self, ctx):
        """Mass bans users from a text file."""
        try:
            users = (await ctx.message.attachments[0].read()).decode().split()
        except Exception as e:
            return await ctx.send(f"Failed to read file: ```py\n{e.__class__.__name__}: {e}\n```")

        await self.execute_massban(ctx, users)

    @mban.command(name='url')
    async def mban_url(self, ctx, url):
        """Mass bans from a pastebin URL. Must be the RAW text url."""
        confirmation = await confirm_action(ctx, "Are you sure this is a valid URL? (Must be the **raw** text!)")

        if confirmation:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        text = await resp.text()
                        users = text.split()
            except Exception as e:
                return await ctx.send(f"Failed to read url: ```py\n{e.__class__.__name__}: {e}\n```")

            await self.execute_massban(ctx, users)

        else:
            await ctx.send("Cancelled!")

    @commands.group(name='invites', aliases=['invite'], invoke_without_command=True)
    async def invites(self, ctx, code=None):
        """Returns information on this server's invites, or on a single invite."""
        invites = await ctx.guild.invites()

        # if a code is provided, info about that invite
        if code:
            invite = discord.utils.get(invites, code=code)

            if not invite:
                return await ctx.send(f"Invite with code {code} not found.")

            return await ctx.send(
                f"__Invite__: `{invite.code}`\n"
                f"> inviter: {invite.inviter} ({invite.inviter.id})\n"
                f"> created_at: {invite.created_at}\n"
                f"> uses: {invite.uses}\n"
            )

        # if no code is provided, general server invite breakdown
        inv_by_mods = 0
        inv_by_bots = 0
        inv_permanent = 0
        inv_unused = 0

        for i in invites:
            if is_mod(i.inviter) and not i.inviter.bot:
                inv_by_mods += 1
            if i.inviter.bot:
                inv_by_bots += 1
            if i.max_age == 0:
                inv_permanent += 1
            if i.uses == 0:
                inv_unused += 1

        await ctx.send(
            f"__Server Invites__:\n"
            f"> total: {len(invites)}\n"
            f"> mods: {inv_by_mods}\n"
            f"> bots: {inv_by_bots}\n"
            f"> permanent: {inv_permanent}\n"
            f"> unused: {inv_unused}\n"
        )

    @invites.command(name='by')
    async def invites_by(self, ctx, who: Union[discord.Member, discord.User, FetchedUser]):
        """Returns a list of invites created by a user."""
        invites = await ctx.guild.invites()
        content = f"__Invites by__: `{who}`\n"

        for i in invites:
            if i.inviter == who:
                content += f"> {i.code} ({i.uses})\n"

        await ctx.send(content)

    # @invites.command(name='created')
    # async def invites_created_since(self, ctx, duration: TimeDelta):
    #     pass
    #
    # @invites.command(name='used')
    # async def invites_used_since(self, ctx, duration: TimeDelta):
    #     pass

    @invites.command(name='delete')
    async def guild_invites_delete(self, ctx, invite_code):
        """Delete an invite."""
        invites = await ctx.guild.invites()
        for invite in invites:
            if invite.code == invite_code:
                try:
                    await invite.delete()
                    return await ctx.send(f"Deleted invite {invite_code}!")
                except Exception as e:
                    return await ctx.send(f"Could not delete invite {invite_code}: ```py\n{e.__class__.__name__}: {e}\n```")
        await ctx.send(f"Could not find invite {invite_code}.")


def setup(bot):
    bot.add_cog(WARNING_EXPERIMENTAL(bot))
