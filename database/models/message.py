from datetime import datetime

from motor.core import Collection


class DiscoMessage:
    def __init__(self, data, collection: Collection):
        self._db = collection

        self.id = data['_id']
        self.author_id = data['author_id']
        self.channel_id = data['channel_id']
        self.guild_id = data['guild_id']
        self.content = data['content']
        self.created_at = datetime.fromtimestamp(data['timestamp'])

    async def edit(self, new_content):
        await self._db.update_one({"_id": self.id}, {"$set": {"content": new_content}})
        self.content = new_content

    async def delete(self):
        await self._db.delete_one({"_id": self.id})
