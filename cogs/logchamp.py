import asyncio
import json
import discord

from collections import defaultdict, deque
from datetime import datetime, timedelta
from discord.ext import commands, tasks
from discord.ext.commands import Cog


# CONFIG = 'src/neptuneshelper/config/logchamp.json'
CONFIG = './logchamp.json'
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


class LogConfig:
    def __init__(self, channel_id, events):
        self.channel_id = channel_id
        self.events = events

    @classmethod
    def load(cls):
        configs = {}

        with open(CONFIG) as fp:
            data = json.load(fp)

        for channel_id, events in data.items():
            i = int(channel_id)
            configs[i] = cls(i, events)

        return configs


class LogMessage:
    def __init__(self, content, file=None):
        self.content = content
        self.file = file


async def dispatch_logs(channel, *logs):
    content = "\n".join(log for log in logs)
    files = [log.file for log in logs]

    await channel.send(
        content, files=files,
        allowed_mentions=discord.AllowedMentions.none())

    return len(logs)


class LogChamp(Cog):
    """YEET"""
    def __init__(self, bot):
        self.bot = bot
        self._to_send = defaultdict(deque)
        self._configs = LogConfig.load()
        self._loops = self.start_dispatch_loops()

    def cog_unload(self):
        for loop in self._loops:
            loop.stop()

    def start_dispatch_loops(self):
        loops = []

        for channel_id in self._configs.keys():

            @tasks.loop(seconds=0.5)
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

                channel = self.bot.get_channel(channel_id)
                n = await dispatch_logs(channel, *logs)
                await asyncio.sleep(0.5*n)

            loops.append(log_dispatch_loop)
            log_dispatch_loop.start()

        return loops

    async def send_log_message(self, channel_id, content, file=None):
        self._to_send[channel_id].append(LogMessage(content, file))

    @Cog.listener()
    async def on_member_join(self, member):
        content = f"{timestamp()} 📥 {member} (`{member.id}`) joined the server (created about {approximate_timedelta(datetime.now() - member.created_at)} ago)"
        for channel_id, events in self._configs:
            if 'member_join' in events:
                await self.send_log_message(channel_id, content)

    @Cog.listener()
    async def on_member_remove(self, member):
        content = f"{timestamp()} 📤 {member} (`{member.id}`) left the server (joined about {approximate_timedelta(datetime.now() - member.joined_at)} ago)"
        for channel_id, events in self._configs:
            if 'member_remove' in events:
                await self.send_log_message(channel_id, content)


def setup(bot):
    bot.add_cog(LogChamp(bot))
