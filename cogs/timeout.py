import asyncio
import datetime
import logging

from discord import AuditLogAction, AuditLogEntry
from discord.ext import commands


logger = logging.getLogger('cogs.modlog')

# log_channel = 713467871040241744
log_channel = 507429352720433152 # plan z

TIMEOUT_START = '👶'
TIMEOUT_END = '🤑'

SECOND = 1
MINUTE = SECOND*60
HOUR = MINUTE*60
DAY = HOUR*24
WEEK = DAY*7


def approximate_timedelta(dt):
    if isinstance(dt, datetime.timedelta):
        dt = dt.total_seconds()
    s = lambda n: 's' if n != 1 else ''
    if dt >= WEEK:
        t = f"{int(_w := dt // WEEK)} week" + s(_w)
    elif dt >= DAY:
        t = f"{int(_d := dt // DAY)} day" + s(_d)
    elif dt >= HOUR:
        t = f"{int(_h := dt // HOUR)} hour" + s(_h)
    elif dt >= MINUTE:
        t = f"{int(_m := dt // MINUTE)} minute" + s(_m)
    else:
        t = f"{int(_s := dt // SECOND)} second" + s(_s)

    return t



class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.audit_id_cache = set()

    async def log_timeout_create(self, user, mod, ends_at, reason):
        duration = approximate_timedelta(ends_at - datetime.datetime.now())
        await self.bot.get_channel(log_channel).send(
            f"{TIMEOUT_START} **MEMBER TIMED OUT**\n"
            f"**User:** {user} (`{user.id}`)\n"
            f"**Duration:** {duration}\n"
            f"**Moderator:** {mod}\n"
            f"**Reason**: {reason.strip()}"
        )

    async def log_timeout_cancel(self, user, mod):
        await self.bot.get_channel(log_channel).send(
            f"{TIMEOUT_END} **MEMBER TIMEOUT CANCELED**\n"
            f"**User:** {user} (`{user.id}`)\n"
            f"**Moderator:** {mod}"
        )

    async def log_timeout_expire(self, user):
        await self.bot.get_channel(log_channel).send(
            f"{TIMEOUT_END} Timeout expired for user {user}"
        )

    async def fetch_audit_log_entry(self, guild, action_type, target):
        async for entry in guild.audit_logs(limit=5):
            if entry.action == action_type and entry.target == target:
                if entry.id in self.audit_id_cache:
                    return
                self.audit_id_cache.add(entry.id)
                return entry

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        member = after
        guild = member.guild

        await asyncio.sleep(5)

        # timeout added
        if after.timeout and not before.timeout:
            logger.info(f"timeout added for {member}")
            entry = await self.fetch_audit_log_entry(guild, AuditLogAction.member_update, member)
            if not entry:
                logger.info("no audit log entry found")
            await self.log_timeout_create(
                member,
                entry.user,
                entry.after.communication_disabled_until,
                entry.reason
            )

        # timeout removed
        elif before.timeout and not after.timeout:
            logger.info(f"timeout removed for {member}")
            entry = await self.fetch_audit_log_entry(guild, AuditLogAction.member_update, member)
            if entry:
                await self.log_timeout_cancel(member, entry.user)
            else:
                await self.log_timeout_expire(member)


def setup(bot):
    bot.add_cog(Timeout(bot))
