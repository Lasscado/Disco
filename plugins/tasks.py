from discord.ext import commands, tasks
from discord import Colour
from utils import avatars
from random import shuffle
from asyncio import sleep

shuffle(avatars) # pra não começar sempre na mesma ordem quando o bot for iniciado

class Tasks(commands.Cog):
    def __init__(self, lite):
        self.lite = lite
        self.avatars = avatars
        self._change_avatar.start()
        self._disconnect_inactive_players.start()

    @tasks.loop(minutes=30)
    async def _change_avatar(self):
        if not self.avatars: # significa que todos os avatares já foram usados
            self.avatars = avatars # repor os avatares
        
        info = self.avatars.pop(0) # pegar o avatar na ordem
        avatar = open(info['path'], 'rb').read()
        rgb = info['rgb'] # alterar a cor dos embeds, baseado na cor do avatar
        self.lite.color = [Colour.from_rgb(*rgb[0]), Colour.from_rgb(*rgb[1])]
        await self.lite.user.edit(avatar=avatar)
        self.lite.log.info('Avatar alterado')

    @tasks.loop(minutes=4)
    async def _disconnect_inactive_players(self):
        self.lite.log.info('Procurando por players inativos')
        for player in self.lite.wavelink.players.values():
            guild = self.lite.get_guild(player.guild_id)
            if not guild or not player.current and not player.queue or not self.has_listeners(guild):
                self.lite.loop.create_task(self._disconnect_player(player))
    
    async def _disconnect_player(self, player):
        await sleep(60)

        guild = self.lite.get_guild(player.guild_id)
        if not guild:
            return await player.destroy()
        elif ((player.current or player.queue) and guild.me.voice and self.has_listeners(guild)):
            return

        self.lite.log.info(f'Iniciando verificação de inatividade em {guild} {guild.id}')

        try:
            await player.disconnect()
            await player.destroy()
        except KeyError:
            pass
        
        await player.send(f'{self.lite.emoji["alert"]} Desconectei do canal de voz porque '
            'ninguém estava me usando para ouvir música.')

    def has_listeners(self, guild):
        return any([m for m in guild.me.voice.channel.members if not m.bot and not m.voice.deaf and not m.voice.self_deaf])

def setup(lite):
    lite.add_cog(Tasks(lite))