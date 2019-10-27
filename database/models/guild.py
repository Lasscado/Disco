from motor.core import Collection


class DiscoGuild:
    def __init__(self, data, collection: Collection):
        self._db = collection

        self.id = data['_id']
        self.options = data['options']

    async def update(self, data):
        await self._db.update_one({"_id": self.id}, {"$set": data})

    async def inc(self, data):
        await self._db.update_one({"_id": self.id}, {"$inc": data})

    async def push(self, data):
        await self._db.update_one({"_id": self.id}, {"$push": data})

    async def pull(self, data):
        await self._db.update_one({"_id": self.id}, {"$pull": data})

    async def delete(self):
        await self._db.delete_one({"_id": self.id})
