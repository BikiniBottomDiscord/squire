import asyncpg
import secrets
import logging
from typing import Optional

from auth import POSTGRES_PASSWORD


logger = logging.getLogger('utils.db')


class Database:
    def __init__(self):
        self.conn: Optional[asyncpg.Connection] = None
        self.by_infraction_id = {}
        self.by_user_id = {}

    async def connect(self):
        if self.conn:
            raise Exception("Already connected to the database.")
        self.conn = await asyncpg.connect(
            user='postgres',
            password=POSTGRES_PASSWORD,
            database='squire',
            host='postgres'
        )

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

    @property
    def is_connected(self):
        return bool(self.conn)

    async def get_infraction(self, inf_id):
        if not self.conn:
            await self.connect()

        if inf_id in self.by_infraction_id:
            return self.by_infraction_id[inf_id]
        infraction = await self.conn.fetchrow('SELECT * FROM infractions WHERE id=($1)', inf_id)
        return infraction

    async def new_infraction(self, moderator_id, user_id, infraction_type, reason):
        if not self.conn:
            await self.connect()

        logger.debug(f"adding infraction {(moderator_id, user_id, infraction_type, reason)}")

        query = 'INSERT INTO infractions (user_id, timestamp, mod_id, infraction, reason, message_id) VALUES ($1, now(), $2, $3, $4, 0) RETURNING id'
        infraction_id = await self.conn.fetchval(query, str(user_id), str(moderator_id), infraction_type, reason)

        query = {
            "mute":   "INSERT INTO user_history (user_id, mute, kick, ban, unmute, unban) VALUES ($1,  $2,  '{}', '{}', '{}', '{}') ON CONFLICT (user_id) DO UPDATE SET mute   = array_cat(mute,   $3) WHERE user_id = $1",
            "kick":   "INSERT INTO user_history (user_id, mute, kick, ban, unmute, unban) VALUES ($1, '{}',  $2,  '{}', '{}', '{}') ON CONFLICT (user_id) DO UPDATE SET kick   = array_cat(kick,   $3) WHERE user_id = $1",
            "ban":    "INSERT INTO user_history (user_id, mute, kick, ban, unmute, unban) VALUES ($1, '{}', '{}',  $2,  '{}', '{}') ON CONFLICT (user_id) DO UPDATE SET ban    = array_cat(ban,    $3) WHERE user_id = $1",
            "unmute": "INSERT INTO user_history (user_id, mute, kick, ban, unmute, unban) VALUES ($1, '{}', '{}', '{}',  $2,  '{}') ON CONFLICT (user_id) DO UPDATE SET unmute = array_cat(unmute, $3) WHERE user_id = $1",
            "unban":  "INSERT INTO user_history (user_id, mute, kick, ban, unmute, unban) VALUES ($1, '{}', '{}', '{}', '{}',  $2 ) ON CONFLICT (user_id) DO UPDATE SET unban  = array_cat(unban,  $3) WHERE user_id = $1",
        }[infraction_type]
        await self.conn.execute(query, user_id, [infraction_id], infraction_id)

        infraction = {'moderator_id': moderator_id, 'user_id': user_id, 'infraction_id': infraction_id, 'infraction_type': infraction_type, 'reason': reason, 'message_id': None}
        self.by_infraction_id[infraction_id] = infraction

        if user_id not in self.by_user_id.keys():
            self.by_user_id[user_id] = {'mute': [], 'ban': [], 'kick': [], 'unmute': [], 'unban': []}
        self.by_user_id[user_id][infraction_type].append(infraction_id)

    async def set_message_id(self, infraction_id, message_id):
        self.by_infraction_id[infraction_id]['message_id'] = message_id
        await self.conn.execute('UPDATE infractions SET message_id = $2 WHERE id = $1', infraction_id, message_id)

    async def edit_infraction(self, infraction_id, reason):
        logger.debug(f"editing infraction {infraction_id} {reason}")
        infraction = self.by_infraction_id[infraction_id]
        # todo: edit in by_user without scanning
        infraction['reason'] = reason

    def get_infractions(self, user_id):
        logger.debug(f"getting infractions for {user_id}")
        return self.by_user_id[user_id]

