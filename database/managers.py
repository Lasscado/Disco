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