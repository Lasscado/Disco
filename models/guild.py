from datetime import datetime

class DiscoGuild:
    def __init__(self, collection, guild_id, register):
        self.db = collection
        self.guild_id = guild_id

        self.data = self.get_data()
        if not self.data and register:
            self.data = self.register()

    def get_data(self):
        return self.db.find_one({"_id": self.guild_id})

    def get_structure(self):
        return {
            "_id": self.guild_id,
            "firstSeen": datetime.utcnow().timestamp(),
            "options": {
                "locale": "en-US",
                "prefix": None,
                "djRole": None,
                "botChannel": None,
                "defaultVolume": None,
                "disabledCommands": [],
                "disabledChannels": [],
                "disabledRoles": [],
                "bannedMembers": []
            }
        }

    def register(self):
        data = self.get_structure()
        self.db.insert_one(data)
        return data

    def update(self, data: dict):
        return self.db.update_one({"_id": self.guild_id}, {"$set": data})

    def insert(self, data: dict):
        return self.db.update_one({"_id": self.guild_id}, {"$push": data})

    def remove(self, data: dict):
        return self.db.update_one({"_id": self.guild_id}, {"$pull": data})

    def delete(self):
        return self.db.delete_one({"_id": self.guild_id})