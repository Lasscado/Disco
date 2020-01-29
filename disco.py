import logging
import traceback
from datetime import datetime
from os import environ, listdir

import i18n
import wavelink
from discord import Game
from discord.ext.commands import AutoShardedBot

from database import DatabaseManager
from utils import emojis, custom_prefix, DiscoPlayer, DEFAULT_EMBED_COLORS


log = logging.getLogger('disco')


class Disco(AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=custom_prefix,
            owner_id=int(environ['OWNER_ID']),
            case_insensitive=True,
            help_command=None,
            max_messages=15000,
            activity=Game(f'Loading...')
        )

        self.db = DatabaseManager(environ['DATABASE_NAME'], environ['DATABASE_URI'])
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
        self.prefixes = environ['PREFIXES'].split(', ')
        self._prefixes = {}
        self._waiting_for_choice = set()
        self._message_logs = set()

    async def on_shard_ready(self, shard_id):
        if shard_id in self.launched_shards:
            log.info(f'Shard {shard_id} reconectada.')
        else:
            self.launched_shards.append(shard_id)
            log.info(f'Shard {shard_id} conectada.')

        guilds = [g for g in self.guilds if g.shard_id == shard_id]
        shard = await self.db.get_shard(shard_id)
        await shard.update(launched_at=datetime.utcnow().timestamp(),
                           latency=self.shards[shard_id].ws.latency,
                           guilds=len(guilds),
                           members=sum(g.member_count for g in guilds if not g.unavailable))

    async def on_ready(self):
        if not self.loaded:
            for plugin in [p[:-3] for p in listdir('plugins') if p.endswith('.py')]:
                try:
                    self.load_extension('plugins.' + plugin)
                except Exception as e:
                    log.error(f'Falha ao carregar o plugin \'{plugin}\':')
                    traceback.print_exception(type(e), e, e.__traceback__)
                else:
                    log.info(f'Plugin {plugin} carregado com sucesso.')

            log.info('Fim de carregamento dos plugins.')

            for ban in await self.db.get_bans(ignore=False):
                if ban.is_guild:
                    self.guild_blacklist.add(ban.target_id)
                else:
                    self.user_blacklist.add(ban.target_id)

            async for guild in self.db._guilds.find({"options.message_logs_channel": {"$ne": None}}):
                self._message_logs.add(guild['_id'])

            log.info('Lista de banidos carregada.')

            self.i18n.load_all_from_path()
            log.info(f'{len(self.i18n.strings)} locale(s) carregada(s).')

            self.loaded = True

        log.info('Sente o GRAVE!')

    async def on_message(self, message):
        self.read_messages += 1

        if not self.loaded or message.author.bot or not message.guild:
            return

        if message.guild.id in self._message_logs:
            self.loop.create_task(self.db.register_message(message))

        if not message.channel.permissions_for(message.guild.me).send_messages:
            return

        if message.content == f'<@!{self.user.id}>':
            message.content += ' whatsmyprefix'

        ctx = await self.get_context(message)
        if (not ctx.valid or ctx.command.cog_name == 'Owner' and ctx.author.id != self.owner_id
                or ctx.author.id in self.user_blacklist or ctx.guild.id in self.guild_blacklist):
            return

        ctx.gdb = await self.db.get_guild(ctx.guild.id)
        options = ctx.gdb.options
        bot_channel = options['bot_channel']
        if ((ctx.channel.id in options['disabled_channels']
             or ctx.command.name in options['disabled_commands']
             or ctx.author.id in options['banned_members']
             or bot_channel and bot_channel != ctx.channel.id
             or any(r for r in ctx.author.roles if r.id in options['disabled_roles']))
                and not ctx.author.guild_permissions.manage_guild):
            return

        ctx.t = self.i18n.get_t(options['locale'])

        if ctx.prefix == f'{ctx.me.mention} ':
            ctx.prefix = f'@{ctx.me.name} '

        try:
            await self.invoke(ctx)
        except Exception as e:
            self.dispatch('command_error', ctx, e)

    def get_player(self, guild_id):
        return self.wavelink.get_player(guild_id, cls=DiscoPlayer)

    def run(self):
        super().run(environ['BOT_TOKEN'])
