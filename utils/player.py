from wavelink.player import Player, Track
from wavelink.events import TrackEnd, TrackException, TrackStuck
from discord import Forbidden, NotFound


class DiscoTrack(Track):
    def __init__(self, requester, _id, info, query=None):
        super().__init__(_id, info, query)

        self.requester = requester
        self.skip_votes = set()


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

    async def hook(self, event):
        if isinstance(event, TrackEnd):
            self.current = None
        elif isinstance(event, (TrackException, TrackStuck)):
            self.repeat = None
            self.current = None
