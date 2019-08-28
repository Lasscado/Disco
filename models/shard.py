from datetime import datetime

class DiscoShard:
    def __init__(self, collection, data):
        self.db = collection

        self.id = data['_id']
        self.created_at = datetime.fromtimestamp(data['createdAt'])
        self.launched_at = datetime.fromtimestamp(data['launchedAt']) if \
            data['launchedAt'] else None
        self.last_update = datetime.fromtimestamp(data['lastUpdate']) if \
            data['lastUpdate'] else None
        self.instance_id = data['instanceId']
        self.latency = data['latency']
        self.guilds = data['guilds']
        self.members = data['members']
        self.players = data['players']

    def update(self, data):
        self.db.update_one({"_id": self.id}, {"$set": {**data,
            "lastUpdate": datetime.utcnow().timestamp()
        }})