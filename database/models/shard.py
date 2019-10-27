from datetime import datetime

from motor.core import Collection


class DiscoShard:
    def __init__(self, data, collection: Collection):
        self._db = collection

        self.id = data['_id']
        self.created_at = datetime.fromtimestamp(data['created_at'])
        self.launched_at = datetime.fromtimestamp(data['launched_at']) if \
            data['launched_at'] else None
        self.last_update = datetime.fromtimestamp(data['last_update']) if \
            data['last_update'] else None
        self.latency = data['latency']
        self.guilds = data['guilds']
        self.members = data['members']
        self.players = data['players']

    async def update(self, data):
        await self._db.update_one({"_id": self.id}, {"$set": {
            **data, "last_update": datetime.utcnow().timestamp()}})

    async def delete(self):
        await self._db.delete_one({"_id": self.id})
