import logging
from datetime import datetime
from os import environ, listdir

import i18n
import wavelink
from discord import Game
from discord.ext.commands import AutoShardedBot

from database import BanManager, GuildManager, ShardManager, db
from utils import emojis, custom_prefix, DEFAULT_EMBED_COLORS
from models import DiscoPlayer

log = logging.getLogger('disco')


class Disco(AutoShardedBot):
    def __init__(self):
        self.prefixes = environ['PREFIXES'].split(', ')
        super().__init__(
            command_prefix=custom_prefix,
            owner_id=int(environ['OWNER_ID']),
            case_insensitive=True,
            help_command=None,
            guild_subscriptions=False,
            max_messages=101,
            activity=Game(f'Prefix: {self.prefixes[0]}')
        )

        self.db = db
        self._bans = BanManager(db.bans)
        self._guilds = GuildManager(db.guilds)
        self._shards = ShardManager(db.shards)
        self.i18n = i18n.I18N(source='pt_BR')
        self.log = log
        self.emoji = emojis
        self.color = DEFAULT_EMBED_COLORS
        self.loaded = False
        self.launched_shards = []
        self.started_at = datetime.utcnow()
        self.wavelink = wavelink.Client(self)
        self.guild_blacklist = set()
        self.user_blacklist = set()
        self.invoked_commands = 0
        self.read_messages = 0
        self.played_tracks = 0
        self._prefixes = {}
        self._waiting_for_choice = set()

    async def on_shard_ready(self, shard_id):
        if shard_id in self.launched_shards:
            return log.info(f'Shard {shard_id} reconectada.')

        self.launched_shards.append(shard_id)
        log.info(f'Shard {shard_id} conectada.')

        guilds = [g for g in self.guilds if g.shard_id == shard_id]
        self._shards.get(shard_id).update({
            "launchedAt": datetime.utcnow().timestamp(),
            "latency": self.shards[shard_id].ws.latency,
            "guilds": len(guilds),
            "members": sum(g.member_count for g in guilds if hasattr(g, '_member_count'))
        })

    async def on_ready(self):
        if not self.loaded:
            for plugin in [p[:-3] for p in listdir('plugins') if p.endswith('.py')]:
                try:
                    self.load_extension('plugins.' + plugin)
                except Exception as e:
                    log.error(f'Falha ao carregar o plugin \'{plugin}\'\n-\n{e.__class__.__name__}: {e}\n-')
                else:
                    log.info(f'Plugin {plugin} carregado com sucesso.')

            log.info('Fim de carregamento dos plugins.')

            for ban in self._bans.find(ignore=False):
                if ban.is_guild:
                    self.guild_blacklist.add(ban.target_id)
                else:
                    self.user_blacklist.add(ban.target_id)

            log.info('Lista de banidos carregada.')

            self.i18n.load_all_from_path()
            log.info(f'{len(self.i18n.strings)} locale(s) carregada(s).')

            self.loaded = True

        log.info('Sente o GRAVE!')

    async def on_message(self, message):
        self.read_messages += 1

        if (not self.loaded or not self.is_ready() or message.author.bot or not message.guild
                or not message.channel.permissions_for(message.guild.me).send_messages):
            return

        if message.content == message.guild.me.mention:
            message.content += ' whatsmyprefix'

        ctx = await self.get_context(message)
        if (not ctx.valid or ctx.command.cog_name == 'Owner' and ctx.author.id != self.owner_id
                or ctx.author.id in self.user_blacklist or ctx.guild.id in self.guild_blacklist):
            return

        ctx._guild = self._guilds.get(ctx.guild.id)
        options = ctx._guild.data['options']
        bot_channel = options['botChannel']
        if ((ctx.channel.id in options['disabledChannels']
             or ctx.command.name in options['disabledCommands']
             or ctx.author.id in options['bannedMembers']
             or bot_channel and bot_channel != ctx.channel.id
             or any(r for r in ctx.author.roles if r.id in options['disabledRoles']))
                and not ctx.author.guild_permissions.manage_guild):
            return

        ctx.locale = options['locale']
        ctx.t = self.i18n.get_t(ctx.locale)

        try:
            await self.invoke(ctx)
        except Exception as e:
            self.dispatch('command_error', ctx, e)

    def get_player(self, guild_id):
        return self.wavelink.get_player(guild_id, cls=DiscoPlayer)

    def run(self):
        super().run(environ['BOT_TOKEN'])
