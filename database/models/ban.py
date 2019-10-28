from datetime import datetime

from motor.core import Collection


class DiscoBan:
    def __init__(self, data, collection: Collection):
        self._db = collection

        self.id = data['_id']
        self.target_id = data['target_id']
        self.author_id = data['author_id']
        self.is_guild = data['is_guild']
        self.reason = data['reason']
        self.date = datetime.utcfromtimestamp(data['date'])
        self.ignore = data['ignore']
        self.ignored_at = datetime.utcfromtimestamp(data['ignored_at']) if data['ignored_at'] \
            else None

    def __str__(self):
        return self.reason

    async def update(self, **kwargs):
        await self._db.update_one({"_id": self.id}, {"$set": kwargs})

    async def ignore(self):
        await self.update(ignore=True, ignored_at=datetime.utcnow().timestamp())
