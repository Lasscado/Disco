from io import StringIO

import discord


class TextUploader:
    def __init__(self, disco, category_id):
        self.disco = disco
        self.category_id = category_id
        self.index = 0

    async def upload(self, file_name, content):
        if not (category := self.disco.get_channel(self.category_id)):
            return

        channel = category.text_channels[self.index % len(category.text_channels)]
        message = await channel.send(file=discord.File(StringIO(content), file_name + '.txt'))
        url = message.attachments[0].url
        self.index += 1
        return 'https://txt.discord.website/?txt=' + url[39:-4], url
