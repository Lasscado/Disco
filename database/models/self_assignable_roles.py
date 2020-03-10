from motor.core import Collection


class DiscoSelfAssignableRoles:
    def __init__(self, data, collection: Collection):
        self._db = collection

        self.guild_id = data['_id']
        self.roles = data['self_assignable_roles']

    async def add(self, role_id):
        await self._db.update_one({"_id": self.guild_id}, {"$push": {"self_assignable_roles": role_id}})

    async def remove(self, role_id):
        await self._db.update_one({"_id": self.guild_id}, {"$pull": {"self_assignable_roles": role_id}})

    async def delete(self):
        await self._db.delete_one({"_id": self.guild_id})
