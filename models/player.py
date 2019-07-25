from wavelink.player import Player
from discord import Forbidden

class DiscoPlayer(Player):
    def __init__(self, bot, guild_id, node):
        super().__init__(bot, guild_id, node)

        self.queue = []
        self.repeat = None
        self.bass_boost = False
        self.text_channel = None

    @property
    def size(self):
        return len(self.queue)

    async def send(self, message):
        try:
            await self.text_channel.send(message)
        except Forbidden:
            pass