from datetime import datetime
from models import *

class BanManager:
    def __init__(self, collection):
        self.db = collection

    @property
    def total(self):
        return self.db.count_documents({})

    def find(self, **kwargs):
        query = self.db.find(kwargs)
        if not query:
            return

        return [DiscoBan(data) for data in query]

    def find_last(self, **kwargs):
        data = self.db.find_one(kwargs).sort('date', -1)
        if not data:
            return

        return DiscoBan(data)

    def find_first(self, **kwargs):
        data = self.db.find_one(kwargs).sort('date', 1)
        if not data:
            return

        return DiscoBan(data)

    def new(self, target_id, author_id, is_guild, reason):
        data = {
            "targetID": target_id,
            "authorID": author_id,
            "isGuild": is_guild,
            "reason": reason,
            "date": datetime.utcnow().timestamp(),
            "ignore": False,
            "ignoredAt": None,
        }

        self.db.insert_one(data)

        return DiscoBan(data)

class GuildManager:
    def __init__(self, collection):
        self.db = collection

    def get(self, guild_id, register = True):
        return DiscoGuild(self.db, guild_id, register)

class ShardManager:
    def __init__(self, collection):
        self.db = collection

    @property
    def total(self):
        return self.db.count_documents({})

    def add(self, shard_id):
        data = {
            "_id": shard_id,
            "createdAt": datetime.utcnow().timestamp(),
            "launchedAt": None,
            "lastUpdate": None,
            "instanceId": None,
            "latency": None,
            "guilds": None,
            "members": None,
            "players": None
        }

        self.db.insert_one(data)

        return data

    def get(self, shard_id, register = True):
        data = self.db.find_one({"_id": shard_id}) or self.add(shard_id) \
            if register else None

        if not data:
            return

        return DiscoShard(self.db, data)

    def all(self, **kwargs):
        query = self.db.find(kwargs).sort('_id', 1)
        if not query:
            return

        return [DiscoShard(self.db, data) for data in query]