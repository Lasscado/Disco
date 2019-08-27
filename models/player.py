from wavelink.player import Player
from discord import Forbidden, NotFound

class DiscoPlayer(Player):
    def __init__(self, bot, guild_id, node):
        super().__init__(bot, guild_id, node)

        self.queue = []
        self.repeat = None
        self.bass_boost = False
        self.text_channel = None
        self.locale = 'pt-BR'

    @property
    def size(self):
        return len(self.queue)

    async def send(self, content=None, embed=None):
        try:
            m = await self.text_channel.send(content=content, embed=embed)
        except Forbidden, NotFound:
            pass
        else:
            return m