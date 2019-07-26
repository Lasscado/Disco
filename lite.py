from discord.ext.commands import AutoShardedBot, when_mentioned_or
from utils import emojis
from os import environ, listdir
from datetime import datetime
from discord import Game
from database import BanManager, GuildManager, db

import logging
import wavelink

log = logging.getLogger('lite')

class DiscoLite(AutoShardedBot):
    def __init__(self):
        prefixes = environ['PREFIXES'].split(', ')
        super().__init__(
            command_prefix=when_mentioned_or(*prefixes),
            owner_id=int(environ['OWNER_ID']),
            case_insensitive=True,
            help_command=None,
            shard_count=1, shard_ids=[0],
            guild_subscriptions=False,
            max_messages=101,
            activity=Game(f'Prefixo: {prefixes[0]}')
        )

        self.db = db
        self._bans = BanManager(db.bans)
        self._guilds = GuildManager(db.guilds)
        self.log = log
        self.emoji = emojis
        self.color = [0xffff00, 0x03001b]
        self.loaded = False
        self.launched_shards = []
        self.started = datetime.utcnow()
        self.wavelink = wavelink.Client(self)
        self.guild_blacklist = set()
        self.user_blacklist = set()
        self.invoked_commands = 0

    async def on_shard_ready(self, shard_id):
        if shard_id in self.launched_shards:
            return log.info(f'Shard {shard_id} reconectada.')

        self.launched_shards.append(shard_id)
        log.info(f'Shard {shard_id} conectada.')

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

            self.loaded = True

        log.info('Sente o GRAVE!')

    async def on_message(self, message):
        if (not self.loaded or not self.is_ready() or message.author.bot or not message.guild
            or not message.channel.permissions_for(message.guild.me).send_messages):
            return

        ctx = await self.get_context(message)
        if (not ctx.valid or ctx.command.hidden and ctx.author.id != self.owner_id
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

        try:
            await self.invoke(ctx)
        except Exception as e:
            self.dispatch('command_error', ctx, e)

    def run(self):
        super().run(environ['BOT_TOKEN'], reconnect=True, bot=True)