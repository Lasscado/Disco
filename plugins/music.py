from discord.ext import commands
from utils import web_url, get_length, checks, l
from models import DiscoPlayer, DiscoTrack
from os import environ
from random import shuffle
from math import ceil
from asyncio import TimeoutError as Timeout

import discord

class Music(commands.Cog):
    def __init__(self, lite):
        self.lite = lite
        self.waiting = set()

        lite.loop.create_task(self.initiate_nodes())

    def cog_unload(self):
        for node in self.lite.wavelink.nodes.values():
            self.lite.loop.create_task(node.destroy())

    def get_player(self, guild_id: int):
        return self.lite.wavelink.get_player(guild_id, cls=DiscoPlayer)

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
            return await player.send(l(player, 'events.queueEnd') % self.lite.emoji["alert"])

        await player.play(track)

        if not player.repeat:
            await player.send(l(player, 'events.trackStart') % (self.lite.emoji["download"],
                track, get_length(track.length), track.requester.name))

    @commands.command(name='play', aliases=['p', 'tocar'])
    @checks.ensure_voice_connection()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _play(self, ctx, *, query):
        if not web_url(query):
            query = f'ytsearch:{query}'

        results = await self.lite.wavelink.get_tracks(query)
        if not results:
            return await ctx.send(l(ctx, 'commands.play.noResults') % (
                self.lite.emoji["false"], ctx.author.name))

        player = ctx.player

        if hasattr(results, 'tracks'):
            total_length = 0
            tracks = results.tracks[:1500-player.size]
            for track in tracks:
                total_length += track.length
                player.queue.append(DiscoTrack(ctx.author, track.id, track.info))

            name = results.data['playlistInfo']['name']
            await player.send(l(ctx, 'commands.play.playlistAdded') % (self.lite.emoji["plus"],
                len(tracks), get_length(total_length), name))
        else:
            if len(results) == 1:
                track = results[0]

                player.queue.append(DiscoTrack(ctx.author, track.id, track.info))

                await player.send(l(ctx, 'commands.play.trackAdded') % (self.lite.emoji["plus"],
                    track, get_length(track.length)))
            else:
                self.waiting.add(ctx.author.id)

                tracks = results[:10]
                options = ''
                for i, track in enumerate(tracks, 1):
                    options += f'**`»`** `{i}` [**{track}**]({track.uri}) `[{get_length(track.length)}]`\n'

                em = discord.Embed(
                    colour=self.lite.color[0],
                    title=l(ctx, 'commands.play.chooseOne'),
                    description=options
                ).set_author(
                    name=l(ctx, 'commands.play.searchResults'),
                    icon_url=ctx.guild.icon_url
                ).set_thumbnail(
                    url=ctx.me.avatar_url
                ).set_footer(
                    text=l(ctx, 'commands.play.typeToCancel')
                )

                q = await player.send(content=ctx.author.mention, embed=em)
                cancel = l(ctx, 'commons.exit').lower()

                try:
                    a = await self.lite.wait_for('message', timeout=120,
                        check=lambda c: c.channel.id == q.channel.id and c.author.id == ctx.author.id \
                            and c.content and (c.content.isdigit() and 0 < int(c.content) <= len(tracks)
                            or c.content.lower() == cancel))
                except Timeout:
                    a = None

                if not a or a.content.lower() == cancel:
                    self.waiting.remove(ctx.author.id)
                    return await q.delete()

                track = tracks[int(a.content) - 1]

                player.queue.append(DiscoTrack(ctx.author, track.id, track.info))
                self.waiting.remove(ctx.author.id)
                await q.edit(content=l(ctx, 'commands.play.trackAdded') % (self.lite.emoji["plus"],
                    track, get_length(track.length)), embed=None)

        if not player.current:
            await player.play(ctx.player.queue.pop(0))
            await player.send(l(ctx, 'events.trackStart') % (self.lite.emoji["download"],
                player.current, get_length(player.current.length), ctx.author.name))

    @commands.command(name='shuffle', aliases=['misturar'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _shuffle(self, ctx):
        shuffle(ctx.player.queue)
        await ctx.player.send(l(ctx, 'commands.shuffle.shuffled') % (
            self.lite.emoji["shuffle"], ctx.author.name))

    @commands.command(name='repeat', aliases=['loop', 'repetir'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _repeat(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying') % (
                self.lite.emoji["false"], ctx.author.name))

        if ctx.player.repeat:
            ctx.player.repeat = None
            await ctx.player.send(l(ctx, 'commands.repeat.disable') % (self.lite.emoji["repeatOne"],
                ctx.author.name, ctx.player.current))
        else:
            ctx.player.repeat = ctx.player.current
            await ctx.player.send(l(ctx, 'commands.repeat.enable') % (self.lite.emoji["repeatOne"],
                ctx.author.name, ctx.player.current))

    @commands.command(name='stop', aliases=['disconnect', 'dc', 'parar', 'sair'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _stop(self, ctx):
        vc = ctx.me.voice.channel
        await ctx.player.disconnect()
        await ctx.player.destroy()
        await ctx.player.send(l(ctx, 'commands.stop.stopped') % (
            self.lite.emoji["true"], vc, ctx.author.name))

    @commands.command(name='volume', aliases=['vol', 'v'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _volume(self, ctx, vol: int):
        if not 0 < vol < 151:
            return await ctx.send(l(ctx, 'commands.volume.invalidValue') % (
                self.lite.emoji["false"], ctx.author.name))

        await ctx.player.set_volume(vol)
        await ctx.player.send(l(ctx, 'commands.volume.changed') % (
            self.lite.emoji["volume"], ctx.author.name, vol))

    @commands.command(name='clear', aliases=['reset', 'limpar'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _clear(self, ctx):
        if not ctx.player.queue:
            return await ctx.send(l(ctx, 'commands.clear.alreadyEmpty') % (
                self.lite.emoji["false"], ctx.author.name))

        ctx.player.queue.clear()
        await ctx.player.send(l(ctx, 'commands.clear.cleaned') % (
            self.lite.emoji["alert"], ctx.author.name))

    @commands.command(name='pause', aliases=['pausar'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _pause(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying') % (
                self.lite.emoji["false"], ctx.author.name))

        if ctx.player.paused:
            await ctx.player.send(l(ctx, 'commands.pause.unpause') % (
                self.lite.emoji["alert"], ctx.author.name))
        else:
            await ctx.player.send(l(ctx, 'commands.pause.pause') % (
                self.lite.emoji["alert"], ctx.author.name))

        await ctx.player.set_pause(not ctx.player.paused)

    @commands.command(name='remove', aliases=['r', 'remover', 'delete', 'del'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _remove(self, ctx, index: int):
        if not ctx.player.queue:
            return await ctx.send(l(ctx, 'errors.emptyQueue') % (
                self.lite.emoji["false"], ctx.author.name))

        try:
            track = ctx.player.queue.pop(index - 1)
        except IndexError:
            return await ctx.send(l(ctx, 'errors.invalidValue') % (
                self.lite.emoji["false"], ctx.author.name))

        await ctx.send(l(ctx, 'commands.remove.removed') % (
                self.lite.emoji["true"], ctx.author.name, track))

    @commands.command(name='playat', aliases=['pa', 'pularpara', 'skt', 'skipto'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _play_at(self, ctx, index: int):
        player = ctx.player
        if not player.queue:
            return await ctx.send(l(ctx, 'errors.emptyQueue') % (
                self.lite.emoji["false"], ctx.author.name))

        try:
            player.queue = player.queue[index - 1:]
            track = player.queue.pop(0)
        except IndexError:
            return await ctx.send(l(ctx, 'errors.invalidValue') % (
                self.lite.emoji["false"], ctx.author.name))

        player.queue.insert(0, track)
        await player.stop()

    @commands.command(name='nowplaying', aliases=['np', 'tocandoagora', 'tocando', 'now'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _now_playing(self, ctx):
        player = self.get_player(ctx.guild.id)
        if not player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying') % (
                self.lite.emoji["false"], ctx.author.name))

        track = player.current
        em = discord.Embed(
            colour=self.lite.color[0],
            description=l(ctx, 'commands.nowplaying.text') % (track, track.uri,
                get_length(track.length), track.requester.mention)
        )

        await ctx.send(embed=em, delete_after=15)

    @commands.command(name='skip', aliases=['s', 'sk', 'skp'])
    @checks.is_voice_connected()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _skip(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying') % (
                self.lite.emoji["false"], ctx.author.name))

        track = ctx.player.current
        if track.requester.id == ctx.author.id:
            await ctx.player.send(l(ctx, 'commands.skip.skippedByRequester') % (
                self.lite.emoji["alert"], track, ctx.author.name))

            return await ctx.player.stop()

        elif ctx.author.id in track.skip_votes:
            return await ctx.send(l(ctx, 'commands.skip.alreadyVotted') % (
                self.lite.emoji["false"], ctx.author.name))

        track.skip_votes.add(ctx.author.id)
        await ctx.player.send(l(ctx, 'commands.skip.voteAdded') % (self.lite.emoji["alert"],
            ctx.author.name, len(track.skip_votes)))

        if len(track.skip_votes) == 3:
            await ctx.player.send(l(ctx, 'commands.skip.skipped') % (
                self.lite.emoji["alert"], track))

            await ctx.player.stop()

    @commands.command(name='forceskip', aliases=['fskip', 'pularagora'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _force_skip(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying') % (
                self.lite.emoji["false"], ctx.author.name))

        await ctx.player.send(l(ctx, 'commands.forceskip.skipped') % (
            self.lite.emoji["alert"], ctx.author.name, ctx.player.current))

        await ctx.player.stop()

    @commands.command(name='bassboost', aliases=['bass', 'boost', 'bb'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _bass_boost(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying') % (
                self.lite.emoji["false"], ctx.author.name))

        if ctx.player.bass_boost:
            await ctx.player.set_preq('flat')
            await ctx.player.send(l(ctx, 'commands.bassboost.disabled') % (
                self.lite.emoji["volume"], ctx.author.name))
        else:
            await ctx.player.set_preq('boost')
            await ctx.player.send(l(ctx, 'commands.bassboost.enabled') % (
                self.lite.emoji["volume"], ctx.author.name))

        ctx.player.bass_boost = not ctx.player.bass_boost

    @commands.command(name='queue', aliases=['q', 'fila', 'lista'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _queue(self, ctx, page: int = 1):
        player = self.get_player(ctx.guild.id)
        if not player.queue:
            return await ctx.send(l(ctx, 'errors.emptyQueue') % (
                self.lite.emoji["false"], ctx.author.name))

        length = get_length(sum(track.length for track in player.queue), True)

        pages = ceil(player.size / 12)
        if not 0 < page <= pages:
            page = 1

        skip = (page - 1) * 12
        current = player.current
        tracks = player.queue[skip:skip+12]

        txt = l(ctx, 'commands.queue.currentTrack') % (current, current.uri,
            get_length(current.length), current.requester.mention)

        for i, track in enumerate(tracks, skip+1):
            txt += l(ctx, 'commands.queue.track') % (i, track, track.uri,
                get_length(track.length), track.requester.mention)

        em = discord.Embed(
            colour=self.lite.color[1],
            title=l(ctx, 'commands.queue.name'),
            description=txt
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url
        ).set_thumbnail(
            url=ctx.me.avatar_url
        ).set_footer(
            text=l(ctx, 'commands.queue.details') % (length, page, pages)
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='reverse', aliases=['rev', 'inverter'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _reverse(self, ctx):
        if not ctx.player.queue:
            return await ctx.send(l(ctx, 'errors.emptyQueue') % (
                self.lite.emoji["false"], ctx.author.name))

        ctx.player.queue.reverse()
        await ctx.player.send(l(ctx, 'commands.reverse.success') % (
                self.lite.emoji["shuffle"], ctx.author.name))

def setup(lite):
    lite.add_cog(Music(lite))