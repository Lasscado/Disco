from datetime import datetime

from motor import motor_asyncio

from .models import DiscoBan, DiscoGuild, DiscoShard


class DatabaseManager:
    def __init__(self, name, uri):
        self._client = motor_asyncio.AsyncIOMotorClient(uri)
        self._db = db = self._client[name]
        self._bans = db.bans
        self._guilds = db.guilds
        self._shards = db.shards

    @property
    async def total_bans(self):
        return await self._bans.count_documents({})

    @property
    async def total_shards(self):
        return await self._shards.count_documents({})

    async def connect(self):
        await self._db.command('ping')

    async def get_guild(self, guild_id, register=True):
        if data := await self._guilds.find_one({"_id": guild_id}):
            return DiscoGuild(data, self._guilds)
        elif register:
            return await self.register_guild(guild_id)

    async def get_bans(self, **kwargs):
        bans = []
        async for data in self._bans.find(kwargs):
            bans.append(DiscoBan(data, self._bans))

        return bans

    async def get_last_ban(self, **kwargs):
        if data := await self._bans.find(kwargs).sort('date', -1).limit(1).to_list(None):
            return DiscoBan(data[0], self._bans)

    async def get_first_ban(self, **kwargs):
        if data := await self._bans.find(kwargs).sort('date', 1).limit(1).to_list(None):
            return DiscoBan(data[0], self._bans)

    def get_shards(self, **kwargs):
        return self._shards.find(kwargs)

    async def get_shard(self, shard_id, register=True):
        if data := await self._shards.find_one({"_id": shard_id}):
            return DiscoShard(data, self._shards)
        elif register:
            return await self.register_shard(shard_id)

    async def register_guild(self, guild_id):
        data = {
            "_id": guild_id,
            "options": {
                "locale": "en_US",
                "prefix": None,
                "dj_role": None,
                "bot_channel": None,
                "default_volume": None,
                "disabled_commands": [],
                "disabled_channels": [],
                "disabled_roles": [],
                "banned_members": []
            }
        }

        await self._guilds.insert_one(data)

        return DiscoGuild(data, self._guilds)

    async def register_ban(self, target_id, author_id, is_guild, reason):
        data = {
            "target_id": target_id,
            "author_id": author_id,
            "is_guild": is_guild,
            "reason": reason,
            "date": datetime.utcnow().timestamp(),
            "ignore": False,
            "ignored_at": None
        }

        await self._bans.insert_one(data)

        return DiscoBan(data, self._bans)

    async def register_shard(self, shard_id):
        data = {
            "_id": shard_id,
            "created_at": datetime.utcnow().timestamp(),
            "launched_at": None,
            "last_update": None,
            "latency": None,
            "guilds": None,
            "members": None,
            "players": None
        }

        await self._shards.insert_one(data)

        return DiscoShard(data, self._shards)
