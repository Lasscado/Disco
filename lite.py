from discord.ext.commands import AutoShardedBot, when_mentioned_or
from utils import emojis
from os import environ, listdir
from datetime import datetime
from discord import Game

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

        self.log = log
        self.emoji = emojis
        self.color = [0x1CFA48, 0x1ED743]
        self.loaded = False
        self.launched_shards = []
        self.started = datetime.utcnow()
        self.wavelink = wavelink.Client(self)

    async def on_shard_ready(self, shard_id):
        if shard_id in self.launched_shards:
            return log.info(f'Shard {shard_id} reconectada.')

        self.launched_shards.append(shard_id)
        log.info(f'Shard {shard_id} conectada.')

    async def on_ready(self):
        if not self.loaded:
            log.info('Carregando plugins...')

            for plugin in [p[:-3] for p in listdir('plugins') if p.endswith('.py')]:
                try:
                    self.load_extension('plugins.' + plugin)
                except Exception as e:
                    log.error(f'Falha ao carregar o plugin \'{plugin}\'\n-\n{e.__class__.__name__}: {e}\n-')
                else:
                    log.info(f'Plugin {plugin} carregado com sucesso.')

            self.loaded = True

        log.info('Sente o GRAVE!')

    async def on_message(self, message):
        if not self.loaded or not self.is_ready() or message.author.bot or not message.guild:
            return

        ctx = await self.get_context(message)
        if not ctx.valid or ctx.command.hidden and ctx.author.id != self.owner_id:
            return

        try:
            await self.invoke(ctx)
        except Exception as e:
            self.dispatch('command_error', ctx, e)

    def run(self):
        super().run(environ['BOT_TOKEN'], reconnect=True, bot=True)