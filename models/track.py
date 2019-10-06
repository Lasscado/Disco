from wavelink.player import Track


class DiscoTrack(Track):
    def __init__(self, requester, _id, info, query=None):
        super().__init__(_id, info, query)

        self.requester = requester
        self.skip_votes = set()
