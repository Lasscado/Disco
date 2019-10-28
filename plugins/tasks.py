from asyncio import sleep
from random import choice
from json import loads
from os import environ

from discord import Colour, Activity, ActivityType
from discord.ext import commands, tasks

from utils import avatars, WEBSITE_URL, PATREON_DONATE_URL, STREAMING_ACTIVITY_URL


class Tasks(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

        # if disco.user.id == int(environ['BOT_ID']):
        #    self._change_avatar.start()

        self._activities = [
            ActivityType.listening,
            ActivityType.watching,
            ActivityType.streaming,
            ActivityType.playing
        ]

        self._change_presence.start()
        self._disconnect_inactive_players.start()
        self._update_shard_stats.start()

    def cog_unload(self):
        if self.disco.user.id == int(environ['BOT_ID']):
            self._change_avatar.cancel()

        self._change_presence.cancel()
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
    async def _change_presence(self):
        messages = loads(open('./data/activities.json', encoding='utf-8').read())
        guilds = sum(shard.guilds for shard in await self.disco.db.get_shards().to_list(None))

        self.disco.log.info('Alterando Presences em todas as Shards...')
        for shard in self.disco.shards:
            activity = choice(self._activities)
            message = choice(messages[activity.name]).format(
                website=WEBSITE_URL,
                prefix=self.disco.prefixes[0],
                guilds=guilds,
                donate=PATREON_DONATE_URL
            )

            await self.disco.change_presence(activity=Activity(type=activity,
                                                               name=message + f' [{shard}]',
                                                               url=STREAMING_ACTIVITY_URL),
                                             shard_id=shard)

        self.disco.log.info('Presences alteradas.')

    @tasks.loop(minutes=1)
    async def _update_shard_stats(self):
        for shard_id in self.disco.launched_shards:
            guilds = [g for g in self.disco.guilds if g.shard_id == shard_id]
            shard = await self.disco.db.get_shard(shard_id)
            await shard.update(latency=self.disco.shards[shard_id].ws.latency,
                               guilds=len(guilds),
                               members=sum(g.member_count for g in guilds if hasattr(g, '_member_count')))

        self.disco.log.info('As estatísticas das Shards foram atualizadas.')

    @tasks.loop(minutes=2)
    async def _disconnect_inactive_players(self):
        self.disco.log.info('Procurando por players inativos')
        for player in self.disco.wavelink.players.values():
            guild = self.disco.get_guild(player.guild_id)
            if guild is None or guild.me.voice is None or player.current is None and not player.queue or \
                    not self.has_listeners(guild):
                self.disco.loop.create_task(self._disconnect_player(player))

    async def _disconnect_player(self, player):
        await sleep(60)

        try:
            player = self.disco.wavelink.players[player.guild_id]
        except KeyError:
            return

        guild = self.disco.get_guild(player.guild_id)
        if guild is None or guild.me.voice is None:
            await player.node._send(op='destroy', guildId=str(player.guild_id))
            del player.node.players[player.guild_id]
            return
        elif (player.current or player.queue) and self.has_listeners(guild):
            return

        self.disco.log.info(f'Desconectando de {guild} {guild.id} devido a inatividade')

        await player.destroy()
        await player.send(player.t('events.disconnectPlayer', {"emoji": self.disco.emoji["alert"]}))

    @staticmethod
    def has_listeners(guild):
        return any(m for m in guild.me.voice.channel.members
                   if not m.bot and not m.voice.deaf and not m.voice.self_deaf)


def setup(disco):
    disco.add_cog(Tasks(disco))
