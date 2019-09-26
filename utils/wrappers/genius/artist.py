class Artist:
    def __init__(self, data):
        self.id = data['id']
        self.url = data['url']
        self.name = data['name']
        self.image_url = data['image_url']
        self.header_image_url = data['header_image_url']

    def __str__(self):
        return self.name
