import asyncpg
import logging
from typing import Optional

from auth import POSTGRES_PASSWORD, IP
from utils.parser import ARGS

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
            host=('postgres' if not ARGS.dev else IP)
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

    async def get_history(self, user_id):
        if not self.conn:
            await self.connect()

        if user_id in self.by_user_id:
            return self.by_user_id[user_id]
        query = 'SELECT * FROM user_history WHERE user_id = $1'
        infractions = await self.conn.fetchrow(query, user_id)
        self.by_user_id[user_id] = infractions
        return infractions

    async def new_infraction(self, moderator_id, user_id, infraction_type, reason):
        if not self.conn:
            await self.connect()

        logger.info(f"adding infraction {(moderator_id, user_id, infraction_type, reason)}")

        query = "INSERT INTO infractions (user_id, timestamp, mod_id, infraction, reason, message_id) VALUES ($1, now(), $2, $3, $4, '0') RETURNING id"
        infraction_id = await self.conn.fetchval(query, user_id, moderator_id, infraction_type, reason)

        in_db = await self.conn.fetchval('SELECT exists(SELECT 1 FROM user_history WHERE user_id = $1)', user_id)
        if in_db:
            await self.conn.execute(f'UPDATE user_history SET {infraction_type} = array_append({infraction_type}, $2) WHERE user_id = $1', user_id, infraction_id)
        else:
            args = ([], [], [], [], [])
            args[['mute', 'kick', 'ban', 'unmute', 'unban'].index(infraction_type)].append(infraction_id)
            await self.conn.execute('INSERT INTO user_history (user_id, mute, kick, ban, unmute, unban) VALUES ($1, $2, $3, $4, $5, $6)', user_id, *args)

        infraction = {'moderator_id': moderator_id, 'user_id': user_id, 'infraction_id': infraction_id, 'infraction_type': infraction_type,
                      'reason': reason, 'message_id': None}
        self.by_infraction_id[infraction_id] = infraction

        if user_id not in self.by_user_id.keys():
            self.by_user_id[user_id] = {'mute': [], 'ban': [], 'kick': [], 'unmute': [], 'unban': []}
        self.by_user_id[user_id][infraction_type].append(infraction_id)

        logger.debug(f"infraction {infraction_id} created.")
        return infraction_id

    async def set_message_id(self, infraction_id, message_id):
        await self.get_infraction(infraction_id)  # for cache
        self.by_infraction_id[infraction_id]['message_id'] = message_id
        query = 'UPDATE infractions SET message_id = $2 WHERE id = $1'
        await self.conn.execute(query, infraction_id, message_id)

    async def set_reason(self, infraction_id, reason):
        # await self.get_infraction(infraction_id)  # for cache
        self.by_infraction_id[infraction_id]['reason'] = reason
        query = 'UPDATE infractions SET reason = $2 WHERE id = $1 RETURNING *'
        return await self.conn.fetchrow(query, infraction_id, reason)

    async def set_mod_id(self, infraction_id, mod_id):
        # await self.get_infraction(infraction_id)  # for cache
        self.by_infraction_id[infraction_id]['mod_id'] = mod_id
        query = 'UPDATE infractions SET mod_id = $2 WHERE id = $1 RETURNING *'
        return await self.conn.fetchrow(query, infraction_id, mod_id)
