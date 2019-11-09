class DiscoModLog:
    def __init__(self, data):
        self.id = data['case_id']
        self.action = data['action']
        self.moderator_id = data['moderator_id']
        self.guild_id = data['guild_id']
        self.channel_id = data['channel_id']
        self.message_id = data['message_id']
