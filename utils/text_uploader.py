from io import StringIO

import discord


class TextUploader:
    def __init__(self, disco, guild_id, category_id):
        guild = disco.get_guild(guild_id)
        self.category = guild.get_channel(category_id)
        self.index = 0

    async def upload(self, file_name, content):
        channel = self.category.text_channels[self.index % len(self.category.text_channels)]
        message = await channel.send(file=discord.File(StringIO(content), file_name + '.txt'))
        attachment = message.attachments[0]
        self.index += 1
        return f'https://txt.discord.website/?txt={channel.id}/{attachment.id}/{file_name}', attachment.url
