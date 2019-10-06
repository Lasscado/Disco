from datetime import datetime


class DiscoBan:
    def __init__(self, data):
        self.target_id = data['targetID']
        self.author_id = data['authorID']
        self.is_guild = data['isGuild']
        self.reason = data['reason']
        self.date = datetime.utcfromtimestamp(data['date'])
        self.ignore = data['ignore']

        if data['ignoredAt']:
            self.ignored_at = datetime.utcfromtimestamp(data['ignoredAt'])
        else:
            data['ignoredAt'] = None

    def __str__(self):
        return self.reason
