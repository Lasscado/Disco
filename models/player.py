from wavelink.player import Player
from discord import Forbidden, NotFound


class DiscoPlayer(Player):
    def __init__(self, bot, guild_id, node):
        super().__init__(bot, guild_id, node)

        self.queue = []
        self.repeat = None
        self.bass_boost = False
        self.text_channel = None
        self.t = bot.i18n.get_t(bot.i18n.source)

    @property
    def size(self):
        return len(self.queue)

    async def send(self, content=None, embed=None):
        channel = self.text_channel
        if channel is None or not channel.permissions_for(channel.guild.me).send_messages:
            return

        try:
            await channel.send(content=content, embed=embed)
        except (Forbidden, NotFound):
            pass
