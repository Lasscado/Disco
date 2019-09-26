from .artist import Artist


class Song:
    def __init__(self, data):
        self.id = data['id']
        self.url = data['url']
        self.title = data['title']
        self.full_title = data['full_title']
        self.title_with_featured = data['title_with_featured']
        self.artist = Artist(data['primary_artist'])
        self.image_url = data['song_art_image_url']

    def __str__(self):
        return self.title
