from discord.ext import commands, tasks
from discord import Colour
from datetime import datetime
from utils import avatars, l
from random import choice
from asyncio import sleep
from os import environ

class Tasks(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

        if disco.user.id == int(environ['BOT_ID']):
            self._change_avatar.start()

        self._disconnect_inactive_players.start()
        self._update_shard_stats.start()

    def cog_unload(self):
        if disco.user.id == int(environ['BOT_ID']):
            self._change_avatar.cancel()

        self._disconnect_inactive_players.cancel()
        self._update_shard_stats.cancel()

    @tasks.loop(minutes=30)
    async def _change_avatar(self):
        info = choice(avatars)
        avatar = open(info['path'], 'rb').read()
        rgb = info['rgb']
        self.disco.color = [Colour.from_rgb(*rgb[0]), Colour.from_rgb(*rgb[1])]
        await self.disco.user.edit(avatar=avatar)
        self.disco.log.info('Avatar alterado')

    @tasks.loop(minutes=1)
    async def _update_shard_stats(self):
        for shard_id in self.disco.launched_shards:
            guilds = [g for g in self.disco.guilds if g.shard_id == shard_id]
            self.disco._shards.get(shard_id).update({
                "instanceId": self.disco.instance_id,
                "latency": self.disco.shards[shard_id].ws.latency,
                "guilds": len(guilds),
                "members": sum(g.member_count for g in guilds)
            })

        self.disco.log.info('As estatísticas das Shards foram atualizadas.')

    @tasks.loop(minutes=4)
    async def _disconnect_inactive_players(self):
        self.disco.log.info('Procurando por players inativos')
        for player in self.disco.wavelink.players.values():
            guild = self.disco.get_guild(player.guild_id)
            if not guild or not guild.me.voice or not player.current and not player.queue or \
                not self.has_listeners(guild):
                self.disco.loop.create_task(self._disconnect_player(player))

    async def _disconnect_player(self, player):
        await sleep(60)

        try:
            player = self.disco.wavelink.players[player.guild_id]
        except KeyError:
            return

        guild = self.disco.get_guild(player.guild_id)
        if not guild or not guild.me.voice:
            await player.node._send(op='destroy', guildId=str(player.guild_id))
            del player.node.players[player.guild_id]
            return
        elif ((player.current or player.queue) and self.has_listeners(guild)):
            return

        self.disco.log.info(f'Desconectando de {guild} {guild.id} devido a inatividade')

        await player.destroy()
        await player.send(l(player.locale, 'events.disconnectPlayer', {
            "emoji": self.disco.emoji["alert"]}))

    @staticmethod
    def has_listeners(guild):
        return any(m for m in guild.me.voice.channel.members if not m.bot and not m.voice.deaf and not m.voice.self_deaf)

def setup(disco):
    disco.add_cog(Tasks(disco))