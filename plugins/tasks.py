from discord.ext import commands, tasks
from discord import Colour
from utils import avatars, l
from random import choice
from asyncio import sleep

class Tasks(commands.Cog):
    def __init__(self, lite):
        self.lite = lite
        self._change_avatar.start()
        self._disconnect_inactive_players.start()

    @tasks.loop(minutes=30)
    async def _change_avatar(self):
        info = choice(avatars)
        avatar = open(info['path'], 'rb').read()
        rgb = info['rgb']
        self.lite.color = [Colour.from_rgb(*rgb[0]), Colour.from_rgb(*rgb[1])]
        await self.lite.user.edit(avatar=avatar)
        self.lite.log.info('Avatar alterado')

    @tasks.loop(minutes=4)
    async def _disconnect_inactive_players(self):
        self.lite.log.info('Procurando por players inativos')
        for player in self.lite.wavelink.players.values():
            guild = self.lite.get_guild(player.guild_id)
            if not guild or not guild.me.voice or not player.current and not player.queue or \
                not self.has_listeners(guild):
                self.lite.loop.create_task(self._disconnect_player(player))

    async def _disconnect_player(self, player):
        await sleep(60)

        try:
            player = self.lite.wavelink.players[player.guild_id]
        except KeyError:
            return

        guild = self.lite.get_guild(player.guild_id)
        if not guild or not guild.me.voice:
            await player.node._send(op='destroy', guildId=str(player.guild_id))
            del player.node.players[player.guild_id]
            return
        elif ((player.current or player.queue) and self.has_listeners(guild)):
            return

        self.lite.log.info(f'Desconectando de {guild} {guild.id} devido a inatividade')

        await player.destroy()
        await player.send(l(player.locale, 'events.disconnectPlayer', {
            "emoji": self.lite.emoji["alert"]}))

    @staticmethod
    def has_listeners(guild):
        return any([m for m in guild.me.voice.channel.members if not m.bot and not m.voice.deaf and not m.voice.self_deaf])

def setup(lite):
    lite.add_cog(Tasks(lite))