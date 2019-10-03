from asyncio import TimeoutError as Timeout
from os import environ
from random import shuffle
from math import ceil

import discord
import genius
from discord.ext import commands

from utils import web_url, get_length, checks, l, MusicError
from models import DiscoPlayer, DiscoTrack


class Music(commands.Cog):
    def __init__(self, disco):
        self.disco = disco
        self.genius = genius.Client(environ['GENIUS_API_TOKEN'])

        disco.loop.create_task(self.initiate_nodes())

    def cog_unload(self):
        for node in self.disco.wavelink.nodes.values():
            self.disco.loop.create_task(node.destroy())

    def get_player(self, guild_id: int):
        return self.disco.wavelink.get_player(guild_id, cls=DiscoPlayer)

    async def initiate_nodes(self):
        for node in eval(environ['LAVALINK_NODES']):
            (await self.disco.wavelink.initiate_node(**node)).set_hook(self.on_track_event)

    async def on_track_event(self, event):
        player = event.player
        if player.repeat:
            track = player.repeat
        elif player.size:
            track = player.queue.pop(0)
        else:
            player.current = None
            return await player.send(l(player, 'events.queueEnd', {
                "emoji": self.disco.emoji["alert"]}))

        await player.play(track)
        self.disco.played_tracks += 1

        if not player.repeat:
            await player.send(l(player, 'events.trackStart', {"track": track,
                "emoji": self.disco.emoji["download"], "length": get_length(track.length)}))

    @commands.command(name='play', aliases=['p', 'tocar'])
    @checks.requires_user_choices()
    @checks.ensure_voice_connection()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _play(self, ctx, *, query):
        if not web_url(query):
            query = f'ytsearch:{query}'

        results = await self.disco.wavelink.get_tracks(query)
        if not results:
            return await ctx.send(l(ctx, 'commands.play.noResults', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        player = ctx.player

        if hasattr(results, 'tracks'):
            total_length = 0
            tracks = results.tracks[:1500-player.size]
            for track in tracks:
                total_length += track.length
                player.queue.append(DiscoTrack(ctx.author, track.id, track.info))

            name = results.data['playlistInfo']['name']
            await player.send(l(ctx, 'commands.play.playlistAdded', {"playlist": name,
                "emoji": self.disco.emoji["plus"], "length": get_length(total_length),
                "added": len(tracks)}))
        else:
            if len(results) == 1:
                track = results[0]

                player.queue.append(DiscoTrack(ctx.author, track.id, track.info))

                await player.send(l(ctx, 'commands.play.trackAdded', {"track": track,
                    "emoji": self.disco.emoji["plus"], "length": get_length(track.length)}))
            else:
                self.disco._waiting_for_choice.add(ctx.author.id)

                tracks = results[:10]
                options = ''
                for i, track in enumerate(tracks, 1):
                    options += f'**`»`** `{i}` [**{track}**]({track.uri}) `[{get_length(track.length)}]`\n'

                cancel = l(ctx, 'commons.exit').lower()

                em = discord.Embed(
                    colour=self.disco.color[0],
                    title=l(ctx, 'commands.play.chooseOne'),
                    description=options
                ).set_author(
                    name=l(ctx, 'commands.play.searchResults'),
                    icon_url=ctx.guild.icon_url
                ).set_thumbnail(
                    url=self.disco.user.avatar_url
                ).set_footer(
                    text=l(ctx, 'commands.play.typeToCancel', {
                        "value": cancel
                    })
                )

                q = await player.send(content=ctx.author.mention, embed=em)

                try:
                    a = await self.disco.wait_for('message', timeout=120,
                        check=lambda c: c.channel.id == q.channel.id and c.author.id == ctx.author.id \
                            and c.content and (c.content.isdigit() and 0 < int(c.content) <= len(tracks)
                            or c.content.lower() == cancel))
                except Timeout:
                    a = None

                if not a or a.content.lower() == cancel:
                    return await q.delete()

                track = tracks[int(a.content) - 1]

                player.queue.append(DiscoTrack(ctx.author, track.id, track.info))

                await q.edit(content=l(ctx, 'commands.play.trackAdded', {"track": track,
                    "emoji": self.disco.emoji["plus"], "length": get_length(track.length)}),
                    embed=None)

        if not player.current:
            await player.play(ctx.player.queue.pop(0))
            await player.send(l(ctx, 'events.trackStart', {"author": ctx.author.name,
                "emoji": self.disco.emoji["download"], "track": player.current,
                "length": get_length(player.current.length)}))
            
            self.disco.played_tracks += 1

    @commands.command(name='shuffle', aliases=['misturar'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _shuffle(self, ctx):
        shuffle(ctx.player.queue)
        await ctx.player.send(l(ctx, 'commands.shuffle.shuffled', {"author": ctx.author.name,
            "emoji": self.disco.emoji["shuffle"]}))

    @commands.command(name='repeat', aliases=['loop', 'repetir'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _repeat(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        if ctx.player.repeat:
            ctx.player.repeat = None
            await ctx.player.send(l(ctx, 'commands.repeat.disable', {"author": ctx.author.name,
                "emoji": self.disco.emoji["repeatOne"], "track": ctx.player.current}))
        else:
            ctx.player.repeat = ctx.player.current
            await ctx.player.send(l(ctx, 'commands.repeat.enable', {"author": ctx.author.name,
                "emoji": self.disco.emoji["repeatOne"], "track": ctx.player.current}))

    @commands.command(name='stop', aliases=['disconnect', 'dc', 'parar', 'sair'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _stop(self, ctx):
        await ctx.player.destroy()
        await ctx.player.send(l(ctx, 'commands.stop.stopped', {"author": ctx.author.name,
            "emoji": self.disco.emoji["true"], "channel": ctx.me.voice.channel}))

    @commands.command(name='volume', aliases=['vol', 'v'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _volume(self, ctx, vol: int):
        if not 0 < vol < 151:
            return await ctx.send(l(ctx, 'commands.volume.invalidValue', {
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        await ctx.player.set_volume(vol)
        await ctx.player.send(l(ctx, 'commands.volume.changed', {"author": ctx.author.name,
            "emoji": self.disco.emoji["volume"], "value": vol}))

    @commands.command(name='clear', aliases=['reset', 'limpar'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _clear(self, ctx):
        if not ctx.player.queue:
            return await ctx.send(l(ctx, 'commands.clear.alreadyEmpty', {
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        ctx.player.queue.clear()
        await ctx.player.send(l(ctx, 'commands.clear.cleaned', {"author": ctx.author.name,
            "emoji": self.disco.emoji["alert"]}))

    @commands.command(name='pause', aliases=['pausar'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _pause(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        if ctx.player.paused:
            await ctx.player.send(l(ctx, 'commands.pause.unpause', {"author": ctx.author.name,
                "emoji": self.disco.emoji["pause"]}))
        else:
            await ctx.player.send(l(ctx, 'commands.pause.pause', {"author": ctx.author.name,
                "emoji": self.disco.emoji["pause"]}))

        await ctx.player.set_pause(not ctx.player.paused)

    @commands.command(name='remove', aliases=['r', 'remover', 'delete', 'del'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _remove(self, ctx, index: int):
        if not ctx.player.queue:
            return await ctx.send(l(ctx, 'errors.emptyQueue', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        try:
            track = ctx.player.queue.pop(index - 1)
        except IndexError:
            return await ctx.send(l(ctx, 'errors.invalidValue', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        await ctx.send(l(ctx, 'commands.remove.removed', {"author": ctx.author.name,
                "emoji": self.disco.emoji["true"], "track": track}))

    @commands.command(name='playat', aliases=['pa', 'pularpara', 'skt', 'skipto'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _play_at(self, ctx, index: int):
        player = ctx.player
        if not player.queue:
            return await ctx.send(l(ctx, 'errors.emptyQueue', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        try:
            player.queue = player.queue[index - 1:]
            track = player.queue.pop(0)
        except IndexError:
            return await ctx.send(l(ctx, 'errors.invalidValue', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        player.queue.insert(0, track)
        await player.stop()

    @commands.command(name='nowplaying', aliases=['np', 'tocandoagora', 'tocando', 'now'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _now_playing(self, ctx):
        player = self.get_player(ctx.guild.id)
        if not player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        track = player.current
        em = discord.Embed(
            colour=self.disco.color[0],
            description=l(ctx, 'commands.nowplaying.text', {"track": track,
                "length": get_length(track.length)})
        )

        await ctx.send(embed=em, delete_after=15)

    @commands.command(name='skip', aliases=['s', 'sk', 'skp'])
    @checks.is_voice_connected()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _skip(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        track = ctx.player.current
        if track.requester.id == ctx.author.id:
            await ctx.player.send(l(ctx, 'commands.skip.skippedByRequester', {"track": track,
                "emoji": self.disco.emoji["alert"], "author": ctx.author.name}))

            return await ctx.player.stop()

        elif ctx.author.id in track.skip_votes:
            return await ctx.send(l(ctx, 'commands.skip.alreadyVoted', {
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        track.skip_votes.add(ctx.author.id)
        await ctx.player.send(l(ctx, 'commands.skip.voteAdded', {"author": ctx.author.name,
            "emoji": self.disco.emoji["alert"], "votes": len(track.skip_votes)}))

        if len(track.skip_votes) == 3:
            await ctx.player.send(l(ctx, 'commands.skip.skipped', {"track": track,
                "emoji": self.disco.emoji["alert"]}))

            await ctx.player.stop()

    @commands.command(name='forceskip', aliases=['fskip', 'pularagora'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _force_skip(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        await ctx.player.send(l(ctx, 'commands.forceskip.skipped', {"track": ctx.player.current,
            "emoji": self.disco.emoji["alert"], "author": ctx.author.name}))

        await ctx.player.stop()

    @commands.command(name='bassboost', aliases=['bass', 'boost', 'bb'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _bass_boost(self, ctx):
        if not ctx.player.current:
            return await ctx.send(l(ctx, 'errors.notPlaying', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        if ctx.player.bass_boost:
            await ctx.player.set_preq('flat')
            await ctx.player.send(l(ctx, 'commands.bassboost.disabled', {
                "emoji": self.disco.emoji["volume"], "author": ctx.author.name}))
        else:
            await ctx.player.set_preq('boost')
            await ctx.player.send(l(ctx, 'commands.bassboost.enabled', {
                "emoji": self.disco.emoji["volume"], "author": ctx.author.name}))

        ctx.player.bass_boost = not ctx.player.bass_boost

    @commands.command(name='queue', aliases=['q', 'fila', 'lista'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _queue(self, ctx, page: int = 1):
        player = self.get_player(ctx.guild.id)
        if not player.queue:
            return await ctx.send(l(ctx, 'errors.emptyQueue', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        length = get_length(sum(track.length for track in player.queue), True)

        per_page = 10
        pages = ceil(player.size / per_page)
        if not 0 < page <= pages:
            page = 1

        skip = (page - 1) * per_page
        current = player.current
        tracks = player.queue[skip:skip+per_page]

        txt = l(ctx, 'commands.queue.currentTrack', {"track": current,
            "length": get_length(current.length)})

        for i, t in enumerate(tracks, skip+1):
            txt += f'**`»`** `{i}` [**{t}**]({t.uri}) `[{get_length(t.length)}]` - {t.requester.mention}\n'

        em = discord.Embed(
            colour=self.disco.color[1],
            title=l(ctx, 'commands.queue.name'),
            description=txt
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url
        ).set_thumbnail(
            url=self.disco.user.avatar_url
        ).set_footer(
            text=l(ctx, 'commands.queue.details', {"length": length,
                "page": page, "pages": pages})
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='reverse', aliases=['rev', 'inverter'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _reverse(self, ctx):
        if not ctx.player.queue:
            return await ctx.send(l(ctx, 'errors.emptyQueue', {"author": ctx.author.name,
                "emoji": self.disco.emoji["false"]}))

        ctx.player.queue.reverse()
        await ctx.player.send(l(ctx, 'commands.reverse.success', {"author": ctx.author.name,
                "emoji": self.disco.emoji["shuffle"]}))

    @commands.command(name='lyrics', aliases=['ly'])
    @commands.bot_has_permissions(embed_links=True)
    @checks.requires_user_choices()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _lyrics(self, ctx, *, query = None):
        if not query:
            if not (ctx.author.voice and ctx.me.voice) \
                    or ctx.author.voice.channel != ctx.me.voice.channel:
                raise commands.UserInputError
                
            playing = self.get_player(ctx.guild.id).current
            if not playing:
                return await ctx.send(l(ctx, 'commands.lyrics.notPlaying', {
                    "emoji": self.disco.emoji['false'], "author": ctx.author.name
                }))

            songs = await self.genius.search(playing.title)
            if not songs:
                return await ctx.send(l(ctx, 'commands.lyrics.currentNotFound', {
                    "emoji": self.disco.emoji['false'], "author": ctx.author.name
                }))
        else:
            songs = await self.genius.search(query)
            if not songs:
                return await ctx.send(l(ctx, 'commands.lyrics.notFound', {
                        "emoji": self.disco.emoji['false'], "author": ctx.author.name
                    }))

        self.disco._waiting_for_choice.add(ctx.author.id)

        options = ''
        for i, song in enumerate(songs, 1):
            options += f'**`»`** `{i}` [**{song} - {song.artist}**]({song.url})\n'

        cancel = l(ctx, 'commons.exit').lower()

        em = discord.Embed(
            colour=self.disco.color[0],
            title=l(ctx, 'commands.lyrics.chooseOne'),
            description=options
        ).set_author(
            name=l(ctx, 'commands.lyrics.searchResults') + ('' if \
                query else ' ' + l(ctx, "commands.lyrics.nowPlaying")),
            icon_url=ctx.guild.icon_url
        ).set_thumbnail(
            url=self.disco.user.avatar_url
        ).set_footer(
            text=l(ctx, 'commands.lyrics.typeToCancel', {
                "value": cancel
            })
        )

        q = await ctx.send(content=ctx.author.mention, embed=em)

        try:
            a = await self.disco.wait_for('message', timeout=120,
                check=lambda c: c.channel.id == q.channel.id and c.author.id == ctx.author.id \
                    and c.content and (c.content.isdigit() and 0 < int(c.content) <= len(songs)
                    or c.content.lower() == cancel))
        except Timeout:
            a = None

        if not a or a.content.lower() == cancel:
            return await q.delete()

        song = songs[int(a.content) - 1]

        lyrics = await self.genius.get_lyrics(song)
        if not lyrics:
            return await ctx.send(l(ctx, 'commands.lyrics.lyricsNotFound', {
                    "emoji": self.disco.emoji['false'], "author": ctx.author.name
                }))

        view_more = l(ctx, "commands.lyrics.viewMore", {"url": song.url})
        if len(lyrics) > 2048:
            lyrics = lyrics[:2048 - len(view_more)] + view_more

        em = discord.Embed(
            colour=self.disco.color[1],
            title=f'{song} - {song.artist}',
            description=lyrics,
            url=song.url
        ).set_thumbnail(
            url=song.image_url
        ).set_author(
            name=l(ctx, 'commands.lyrics.songLyrics'),
            icon_url=self.disco.user.avatar_url
        ).set_footer(
            text=str(ctx.author)
        )

        try:
            await q.edit(content=None, embed=em)
        except discord.NotFound:
            pass


def setup(disco):
    disco.add_cog(Music(disco))
