from datetime import datetime


class DiscoCommandHistoryEntry:
    def __init__(self, data):
        self.id = data['_id']
        self.command = data['command']
        self.user_id = data['user_id']
        self.guild_id = data['guild_id']
        self.channel_id = data['channel_id']
        self.invoked_at = datetime.fromtimestamp(data['timestamp'])
        self.duration = data['duration']

    def __str__(self):
        return self.command
