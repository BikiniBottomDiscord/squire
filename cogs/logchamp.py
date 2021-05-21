import asyncio
import json
import discord

from collections import defaultdict, deque
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from discord.ext.commands import Cog


# CONFIG = 'src/neptuneshelper/config/logchamp.json'
CONFIG_FILE = './logchamp.json'
EVENTS = [
    'member_join',
]

SECOND = 1
MINUTE = SECOND*60
HOUR = MINUTE*60
DAY = HOUR*24
WEEK = DAY*7
MONTH = DAY*30
YEAR = DAY*365


def s(n):
    return 's' if n != 1 else ''


def approximate_timedelta(dt):
    if isinstance(dt, timedelta):
        dt = dt.total_seconds()
    if dt >= YEAR:
        t = f"{int(_y := dt // YEAR)} year" + s(_y)
    elif dt >= MONTH:
        t = f"{int(_mo := dt // MONTH)} month" + s(_mo)
    elif dt >= WEEK:
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


def timestamp():
    return datetime.now().strftime("`[%H:%M:%S]`")


def ago(t):
    return approximate_timedelta(datetime.utcnow() - t)


def format_user(u):
    if not u:
        return None
    if isinstance(u, dict):
        return f"{u.get('username')}#{u.get('discriminator')} (`{u.get('id')}`)"
    else:
        return f"{u} (`{u.id}`)"


def load_config():
    configs = defaultdict(list)
    channels = []

    with open(CONFIG_FILE) as fp:
        data = json.load(fp)
        guild = data['GUILD']
        logs = data['LOGS']

    for channel_id, events in logs.items():
        i = int(channel_id)
        channels.append(i)
        for event in events:
            configs[event].append(i)

    return guild, channels, configs


GUILD, CHANNELS, LOG_CONFIG = load_config()


class LogMessage:
    def __init__(self, content, file=None):
        self.content = content
        self.file = file


async def dispatch_logs(channel, *logs):
    content = "\n".join(log.content for log in logs)
    files = [log.file for log in logs if log.file]

    await channel.send(
        content, files=files,
        allowed_mentions=discord.AllowedMentions.none())

    return len(logs)


class LogChamp(Cog):
    """YEET"""
    def __init__(self, bot):
        self.bot = bot
        self._to_send = defaultdict(deque)
        self._loops = self.start_dispatch_loops()

    def cog_unload(self):
        for loop in self._loops:
            loop.stop()

    def start_dispatch_loops(self):
        loops = []

        for channel_id in CHANNELS:

            @tasks.loop(seconds=1)
            async def log_dispatch_loop():
                await self.bot.wait_until_ready()
                logs = []

                while True:
                    if len(logs) >= 5:
                        break
                    try:
                        logs.append(self._to_send[channel_id].popleft())
                    except IndexError:
                        break

                if logs:
                    channel = self.bot.get_channel(channel_id)
                    n = await dispatch_logs(channel, *logs)
                    await asyncio.sleep(0.5*n)

            loops.append(log_dispatch_loop)
            log_dispatch_loop.start()

        return loops

    async def send_log_message(self, type, content, file=None):
        for channel_id in LOG_CONFIG[type]:
            self._to_send[channel_id].append(LogMessage(content, file))

    @Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id != GUILD:
            return
        content = f"{timestamp()} 📥 {format_user(member)} joined the server (created about {ago(member.created_at)} ago)"
        await self.send_log_message('member_join', content)

    @Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != GUILD:
            return
        content = f"{timestamp()} 📤 {format_user(member)} left the server (joined about {ago(member.joined_at)} ago)"
        await self.send_log_message('member_remove', content)

    @Cog.listener()
    async def on_raw_message_edit(self, payload):
        if payload.guild_id != GUILD:
            return
        after = payload.data.get('content')
        if payload.cached_message:
            if payload.cached_message.content == after:
                return
            before = payload.cached_message.content
            author = payload.cached_message.author
        else:
            before = None
            author = payload.data.get('author')
            author = self.bot.get_user(author) or author
        cid = payload.channel_id
        created_at = discord.utils.snowflake_time(payload.message_id)
        content = f"{timestamp()} 📝 message by {format_user(author)} in <#{cid}> has been edited (sent about {ago(created_at)} ago)\n" \
                  f"**Old**: {before}\n" \
                  f"**New**: {after}"
        await self.send_log_message('message_edit', content)

    @Cog.listener()
    async def on_raw_message_delete(self, payload):
        if payload.guild_id != GUILD:
            return
        if payload.cached_message:
            before_msg = payload.cached_message
            before = payload.cached_message.content
            author = payload.cached_message.author
        else:
            before_msg = before = author = None
        cid = payload.channel_id
        created_at = discord.utils.snowflake_time(payload.message_id)
        content = f"{timestamp()} 🗑 message by {format_user(author)} in <#{cid}> has been deleted (sent about {ago(created_at)} ago)\n" \
                  f"**Content**: {before}"
        if before_msg and before_msg.attachments:
            urls = ', '.join(a.url for a in before_msg.attachments)
            content += f"\n({urls})"
        await self.send_log_message('message_delete', content)


def setup(bot):
    bot.add_cog(LogChamp(bot))
