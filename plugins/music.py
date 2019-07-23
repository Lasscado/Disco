from discord.ext import commands
from utils import DiscoLitePlayer, DiscoLiteTrack, MusicError, web_url, get_length, checks
from os import environ
from random import shuffle
from math import ceil

import discord

class Music(commands.Cog, name='Música'):
    def __init__(self, lite):
        self.lite = lite

        lite.loop.create_task(self.initiate_nodes())
    
    def cog_unload(self):
        for node in self.lite.wavelink.nodes.values():
            self.lite.loop.create_task(node.destroy())

    def get_player(self, guild_id: int):
        return self.lite.wavelink.get_player(guild_id, cls=DiscoLitePlayer)

    async def initiate_nodes(self):
        for node in eval(environ['LAVALINK_NODES']):
            (await self.lite.wavelink.initiate_node(**node)).set_hook(self.on_track_event)

    async def on_track_event(self, event):
        player = event.player
        if player.repeat:
            track = player.repeat
        elif player.size:
            track = player.queue.pop(0)
        else:
            player.current = None
            return await player.send(f'{self.lite.emoji["alert"]} A fila de reprodução acabou.')

        await player.play(track)
        
        if not player.repeat:
            await player.send(f'{self.lite.emoji["download"]} Tocando agora: **`{track}`** '
                f'`({get_length(track.length)})`. Requisitado por **{track.requester.name}**.')

    @commands.command(name='play', aliases=['p', 'tocar'], usage='<Nome|URL>',
        description='Busca e adiciona a música especificada na fila de reprodução.')
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _play(self, ctx, *, query):
        if not web_url(query):
            query = f'ytsearch:{query}'

        results = await self.lite.wavelink.get_tracks(query)
        if not results:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, não '
                'consegui obter nenhum resultado para sua busca.')

        player = ctx.player

        if hasattr(results, 'tracks'):
            total_length = 0
            for track in results.tracks[:1500-player.size]:
                total_length += track.length
                player.queue.append(DiscoLiteTrack(ctx.author, track.id, track.info))

            name = results.data['playlistInfo']['name']
            await player.send(f'{self.lite.emoji["plus"]} Adicionei **{len(results.tracks)}** '
                f'faixas `({get_length(total_length)})` da playlist **`{name}`** na fila.')
        else:
            track = results[0]
            player.queue.append(DiscoLiteTrack(ctx.author, track.id, track.info))
            await player.send(f'{self.lite.emoji["plus"]} Adicionei **`{track}`** '
                f'`({get_length(track.length)})` na fila.')

        if not player.current:
            await player.play(ctx.player.queue.pop(0))
            await player.send(f'{self.lite.emoji["download"]} Tocando agora: '
                f'**`{player.current}`** `({get_length(player.current.length)})`. Requisitado por '
                f'**{ctx.author.name}**.')

    @commands.command(name='shuffle', aliases=['misturar'],
        description='Mistura as faixas da fila de reprodução.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _shuffle(self, ctx):
        shuffle(ctx.player.queue)
        await ctx.player.send(f'{self.lite.emoji["shuffle"]} **{ctx.author.name}**, você misturou '
            'a fila de reprodução.')

    @commands.command(name='repeat', aliases=['loop', 'repetir'],
        description='Coloca em loop, a música que estiver tocando.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _repeat(self, ctx):
        if not ctx.player.current:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, eu não estou'
                ' tocando nada no momento.')
        
        if ctx.player.repeat:
            ctx.player.repeat = None
            await ctx.player.send(f'{self.lite.emoji["repeatOne"]} **{ctx.author.name}**, você desativou o modo'
                f' repetição para a faixa **`{ctx.player.current}`**.')
        else:
            ctx.player.repeat = ctx.player.current
            await ctx.player.send(f'{self.lite.emoji["repeatOne"]} **{ctx.author.name}**, você ativou o '
                f'modo repetição para a faixa **`{ctx.player.current}`**.')

    @commands.command(name='stop', aliases=['disconnect', 'dc', 'parar', 'sair'],
        description='Limpa a fila de reprodução e desconecta o bot do canal de voz.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _stop(self, ctx):
        vc = ctx.me.voice.channel
        await ctx.player.disconnect()
        await ctx.player.destroy()
        await ctx.player.send(f'{self.lite.emoji["true"]} Limpei a fila & desconectei do canal '
            f'**`{vc}`** a pedido de **{ctx.author.name}**.')

    @commands.command(name='volume', aliases=['vol', 'v'], usage='<1-150>',
        description='Aumenta ou diminui o volume do player.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _volume(self, ctx, vol: int):
        if not 0 < vol < 151:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você deve '
                'fornecer um valor entre **`1`** e **`150`**.')

        await ctx.player.set_volume(vol)
        await ctx.player.send(f'{self.lite.emoji["volume"]} **{ctx.author.name}** alterou o volume do '
            f'player para **`{vol}%`**.')

    @commands.command(name='clear', aliases=['reset', 'limpar'],
        description='Limpa a fila de reprodução.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _clear(self, ctx):
        if not ctx.player.queue:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, a fila de '
                'reprodução já está vazia.')

        ctx.player.queue.clear()
        await ctx.player.send(f'{self.lite.emoji["alert"]} A fila de reprodução foi limpa por '
            f'**{ctx.author.name}**.')

    @commands.command(name='pause', aliases=['pausar'],
        description='Pausa e despausa a música que estiver tocando no momento.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _pause(self, ctx):
        if not ctx.player.current:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, eu não '
                'estou tocando nada no momento.')

        await ctx.player.set_pause(not ctx.player.paused)
        
        if ctx.player.paused:
            await ctx.player.send(f'{self.lite.emoji["alert"]} **{ctx.author.name}** pausou o player.')
        else:
            await ctx.player.send(f'{self.lite.emoji["alert"]} **{ctx.author.name}** despausou o player.')

    @commands.command(name='remove', aliases=['r', 'remover', 'delete', 'del'], usage='<Posição>',
        description='Remove uma faixa especifica da fila de reprodução.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _remove(self, ctx, index: int):
        if not ctx.player.queue:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, a fila de '
                'reprodução está vazia.')

        try:
            track = ctx.player.queue.pop(index - 1)
        except IndexError:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você '
                'forneceu um valor inválido.')

        await ctx.send(f'{self.lite.emoji["true"]} **{ctx.author.name}**, você removeu a faixa '
            f'**`{track}`** da fila de reprodução.')

    @commands.command(name='playat', aliases=['pa', 'pularpara', 'skt', 'skipto'], usage='<Posição>',
        description='Pula para uma faixa especifica.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _play_at(self, ctx, index: int):
        player = ctx.player
        if not player.queue:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, a fila de '
                'reprodução está vazia.')

        try:
            player.queue = player.queue[index - 1:]
            track = player.queue.pop(0)
        except IndexError:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você '
                'forneceu um valor inválido.')

        player.queue.insert(0, track)
        await player.stop()

    @commands.command(name='nowplaying', aliases=['np', 'tocandoagora', 'tocando', 'now'],
        description='Mostra detalhes sobre a música que estiver tocando.')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _now_playing(self, ctx):
        player = self.get_player(ctx.guild.id)
        if not player.current:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, eu não '
                'estou tocando nada no momento.')

        track = player.current
        em = discord.Embed(
            colour=self.lite.color[0],
            description=f'Tocando Agora: **[{track}]({track.uri})** '
                f'`({get_length(track.length)})` - {track.requester.mention}'
        )

        await ctx.send(embed=em, delete_after=15)

    @commands.command(name='skip', aliases=['s', 'sk', 'skp'],
        description='Vota para pular a música que estiver tocando.')
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _skip(self, ctx):
        if not ctx.player.current:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, eu não estou'
                ' tocando nada no momento.')

        track = ctx.player.current
        if track.requester.id == ctx.author.id:
            await ctx.player.send(f'{self.lite.emoji["alert"]} A faixa **`{track}`** foi pulada por '
                f'quem a adicionou. (**{ctx.author.name}**)')
            
            return await ctx.player.stop()

        elif ctx.author.id in track.skip_votes:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você já '
                'votou para pular essa faixa.')
        
        track.skip_votes.add(ctx.author.id)
        await ctx.player.send(f'{self.lite.emoji["alert"]} **{ctx.author.name}** votou para pular '
            f'a música atual. **`({len(track.skip_votes)}/3)`**')

        if len(track.skip_votes) == 3:
            await ctx.player.send(f'{self.lite.emoji["alert"]} A faixa **`{track}`** foi pulada pois '
                'atingiu a quantia de votos necessários.')
            
            await ctx.player.stop()

    @commands.command(name='forceskip', aliases=['fskip', 'pularagora'],
        description='Força pular a música que estiver tocando.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _force_skip(self, ctx):
        if not ctx.player.current:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, eu não estou'
                ' tocando nada no momento.')

        await ctx.player.send(f'{self.lite.emoji["alert"]} **{ctx.author.name}** pulou a faixa '
            f'**`{ctx.player.current}`** a força.')
        
        await ctx.player.stop()

    @commands.command(name='bassboost', aliases=['bass', 'boost', 'bb'],
        description='Ativa e desativa o Modo Bass Boost (mais graves).')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _bass_boost(self, ctx):
        if not ctx.player.current:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, eu não estou'
                ' tocando nada no momento.')

        if ctx.player.bass_boost:
            await ctx.player.set_preq('flat')
            await ctx.player.send(f'{self.lite.emoji["volume"]} **{ctx.author.name}** desativou o '
                'modo **`BASS BOOST`**.')
        else:
            await ctx.player.set_preq('boost')
            await ctx.player.send(f'{self.lite.emoji["volume"]} **{ctx.author.name}** ativou o '
                'modo **`BASS BOOST`**. Sente o grave!')

        ctx.player.bass_boost = not ctx.player.bass_boost

    @commands.command(name='queue', aliases=['q', 'fila', 'lista'], usage='[Página]',
        description='Lista todas as faixas da fila de reprodução.')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _queue(self, ctx, page: int = 1):
        player = self.get_player(ctx.guild.id)
        if not player.queue:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, a fila de '
                'reprodução está vazia.')

        length = get_length(sum(track.length for track in player.queue), True)

        pages = ceil(player.size / 12)
        if not 0 < page <= pages:
            page = 1

        skip = (page - 1) * 12
        current = player.current
        
        txt = f'Tocando Agora: [**{current}**]({current.uri}) `[{get_length(current.length)}]` - {current.requester.mention}\n\n'
        for i in range(skip, skip + 12):
            try:
                track = player.queue[i]
            except IndexError:
                continue
            
            txt += f'**`»`** `{i+1}` [**{track}**]({track.uri}) `[{get_length(track.length)}]` - {track.requester.mention}\n'

        em = discord.Embed(
            colour=self.lite.color[1],
            title='Fila de Reprodução',
            description=txt
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url
        ).set_thumbnail(
            url=ctx.me.avatar_url
        ).set_footer(
            text=f'Duração: {length} | Página {page}/{pages}'
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='reverse', aliases=['rev', 'inverter'],
        description='Inverte as faixas da fila de reprodução.')
    @checks.staffer_or_role('DJ')
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _reverse(self, ctx):
        if not ctx.player.queue:
            return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, a fila de '
                'reprodução está vazia.')

        ctx.player.queue.reverse()
        await ctx.player.send(f'{self.lite.emoji["shuffle"]} **{ctx.author.name}**, você inverteu'
            ' a fila de reprodução.')

    @_shuffle.before_invoke
    @_repeat.before_invoke
    @_stop.before_invoke
    @_volume.before_invoke
    @_clear.before_invoke
    @_pause.before_invoke
    @_remove.before_invoke
    @_play_at.before_invoke
    @_skip.before_invoke
    @_force_skip.before_invoke
    @_bass_boost.before_invoke
    @_reverse.before_invoke
    async def _check_if_is_connected(self, ctx):
        if not ctx.me.voice:
            raise MusicError(f'{self.lite.emoji["false"]} **{ctx.author.name}**, eu não estou '
                'conectado em nenhum canal de voz.')

        if not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
            raise MusicError(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você precisa '
                'estar conectado ao meu canal de voz para usar esse comando.')
        
        ctx.player = self.get_player(ctx.guild.id)

        return True

    @_play.before_invoke
    async def _before_play(self, ctx):
        ctx.player = player = self.get_player(ctx.guild.id)
        if not ctx.me.voice:
            if not ctx.author.voice:
                raise MusicError(f'{self.lite.emoji["false"]} **{ctx.author.name}**, '
                    'você precisa estar conectado em um canal de voz para usar esse comando.')

            vc = ctx.author.voice.channel
            perms = vc.permissions_for(ctx.me)

            if not perms.connect or not perms.speak:
                raise MusicError(f'{self.lite.emoji["false"]} **{ctx.author.name}**, '
                    'eu preciso das permissões **`CONECTAR`** e **`FALAR`** no seu canal de voz.')

            if vc.user_limit and len(vc.members) + 1 > vc.user_limit and not perms.administrator:
                raise MusicError(f'{self.lite.emoji["false"]} **{ctx.author.name}**, '
                    'seu canal de voz está lotado!')

            player.text_channel = ctx.channel
            await player.connect(vc.id)
            await ctx.send(f'{self.lite.emoji["wireless"]} Me conectei ao canal de voz **`{vc}`**.')
        
        elif not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
            raise MusicError(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você precisa '
                'estar conectado ao meu canal de voz para usar esse comando.')
        
        elif player.size > 1499:
            raise MusicError(f'{self.lite.emoji["false"]} **{ctx.author.name}**, a fila '
                 'de reprodução desse servidor está lotada! Remova alguma faixa ou tente '
                 'novamente mais tarde.')

        return True

def setup(lite):
    lite.add_cog(Music(lite))