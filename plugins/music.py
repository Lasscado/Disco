import re
from asyncio import TimeoutError as Timeout
from datetime import timedelta
from os import environ
from random import shuffle
from math import ceil

import aioredis
import discord
from discord.ext import commands
from wavelink.events import TrackStart, TrackEnd, TrackException, TrackStuck
from wavelink.eqs import Equalizer

from utils import web_url, get_length, checks, DiscoTrack


SEEK_RX = re.compile('^[+-]?(?:([0-9]{1,2}):)?(?:([0-9]{1,2}):)?([0-9]{1,2})$')


class Music(commands.Cog):
    def __init__(self, disco):
        self.disco = disco
        self.redis = None

        for node in disco.wavelink.nodes.values():
            node.set_hook(self.on_track_event)

        disco.loop.create_task(self.create_redis())

    def cog_unload(self):
        if self.redis is not None:
            self.redis.close()

    async def create_redis(self):
        self.redis = await aioredis.create_redis_pool(environ['PRESENCE_REDIS_URI'])

    async def on_track_event(self, event):
        player = event.player

        if isinstance(event, TrackStart):
            self.disco.played_tracks += 1
            track = player.current

            if not player.repeat:
                await player.send(player.t('events.trackStart', {"track": track,
                                                                 "emoji": self.disco.emoji["download"],
                                                                 "length": 'LIVESTREAM' if track.is_stream else
                                                                 get_length(track.length)}))

            if self.redis and (vc := self.disco.get_channel(int(player.channel_id))) and vc.members:
                payload = {
                    "type": "track_start",
                    "track": {
                        "title": track.title,
                        "author": track.author,
                        "length": track.length,
                        "stream": track.is_stream
                    },
                    "users": [member.id for member in vc.members if not member.bot]
                }

                await self.redis.publish_json('activity', payload)

        elif isinstance(event, TrackEnd):
            if player.repeat:
                track = player.repeat
            elif player.size:
                track = player.queue.pop(0)
            else:
                await player.send(player.t('events.queueEnd', {"emoji": self.disco.emoji["alert"]}))

                if self.redis and (vc := self.disco.get_channel(int(player.channel_id))) and vc.members:
                    payload = {
                        "type": "queue_end",
                        "users": [member.id for member in vc.members if not member.bot]
                    }

                    await self.redis.publish_json('activity', payload)

                return

            await player.play(track)

        elif isinstance(event, TrackException):
            track = await self.disco.wavelink.build_track(event.track)
            await player.send(player.t('errors.trackException', {"emoji": self.disco.emoji["alert"],
                                                                 "track": track.title,
                                                                 "error": event.error}))
        elif isinstance(event, TrackStuck):
            track = await self.disco.wavelink.build_track(event.track)
            await player.send(player.t('errors.trackStuck', {"emoji": self.disco.emoji["alert"],
                                                             "track": track.title,
                                                             "threshold": event.threshold}))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and (channel := before.channel) and channel != after.channel \
                and member.guild.me in channel.members and self.redis:
            payload = {
                "type": "user_left",
                "users": [member.id]
            }

            await self.redis.publish_json('activity', payload)

    @commands.command(name='play', aliases=['p', 'tocar'])
    @checks.ensure_voice_connection()
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _play(self, ctx, *, query):
        if not web_url(query):
            query = f'ytsearch:{query}'

        results = await self.disco.wavelink.get_tracks(query)
        if not results:
            return await ctx.send(ctx.t('commands.play.noResults', {"author": ctx.author.name,
                                                                    "emoji": self.disco.emoji["false"]}))

        player = ctx.player
        player.waiting_for_music_choice.add(ctx.author.id)

        if hasattr(results, 'tracks'):
            total_length = 0
            tracks = results.tracks[:1500 - player.size]
            for track in tracks:
                total_length += 0 if track.is_stream else track.length
                player.queue.append(DiscoTrack(ctx.author, track.id, track.info))

            name = results.data['playlistInfo']['name']
            await ctx.send(ctx.t('commands.play.playlistAdded', {"playlist": name,
                                                                 "emoji": self.disco.emoji["plus"],
                                                                 "length": get_length(total_length),
                                                                 "added": len(tracks)}))
        else:
            if len(results) == 1:
                track = results[0]

                player.queue.append(DiscoTrack(ctx.author, track.id, track.info))

                await ctx.send(ctx.t('commands.play.trackAdded', {"track": track,
                                                                  "emoji": self.disco.emoji["plus"],
                                                                  "length": 'LIVESTREAM' if track.is_stream else
                                                                  get_length(track.length)}))
            else:
                tracks = results[:8]
                options = '\n'.join(f'**`»`** `{i}` [**{track}**]({track.uri}) `[{get_length(track.length)}]`'
                                    for i, track in enumerate(tracks, 1))

                cancel = ctx.t('commons.exit').lower()

                em = discord.Embed(
                    colour=self.disco.color[0],
                    title=ctx.t('commands.play.chooseOne'),
                    description=options
                ).set_author(
                    name=ctx.t('commands.play.searchResults'),
                    icon_url=ctx.guild.icon_url
                ).set_thumbnail(
                    url=self.disco.user.avatar_url
                ).set_footer(
                    text=ctx.t('commands.play.typeToCancel', {
                        "value": cancel
                    })
                )

                q = await ctx.send(content=ctx.author.mention, embed=em)

                def check(m):
                    return m.channel.id == q.channel.id and m.author.id == ctx.author.id and m.content \
                        and (m.content.isdecimal() and 0 < int(m.content) <= len(tracks) or m.content.lower() == cancel)

                try:
                    a = await self.disco.wait_for('message', timeout=120, check=check)
                except Timeout:
                    a = None

                if not a or a.content.lower() == cancel:
                    return await q.delete()

                track = tracks[int(a.content) - 1]

                player.queue.append(DiscoTrack(ctx.author, track.id, track.info))

                await q.edit(content=ctx.t('commands.play.trackAdded', {"track": track,
                                                                        "emoji": self.disco.emoji["plus"],
                                                                        "length": get_length(track.length)}),
                             embed=None)

        if not player.current:
            await player.play(ctx.player.queue.pop(0))

    @commands.command(name='shuffle', aliases=['misturar'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _shuffle(self, ctx):
        shuffle(ctx.player.queue)
        await ctx.send(ctx.t('commands.shuffle.shuffled', {"author": ctx.author.name,
                                                           "emoji": self.disco.emoji["shuffle"]}))

    @commands.command(name='repeat', aliases=['loop', 'repetir'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _repeat(self, ctx):
        if not ctx.player.current:
            return await ctx.send(ctx.t('errors.notPlaying', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        if ctx.player.repeat:
            ctx.player.repeat = None
            await ctx.send(ctx.t('commands.repeat.disable', {"author": ctx.author.name,
                                                             "emoji": self.disco.emoji["repeatOne"],
                                                             "track": ctx.player.current}))
        else:
            ctx.player.repeat = ctx.player.current
            await ctx.send(ctx.t('commands.repeat.enable', {"author": ctx.author.name,
                                                            "emoji": self.disco.emoji["repeatOne"],
                                                            "track": ctx.player.current}))

    @commands.command(name='stop', aliases=['disconnect', 'dc', 'parar', 'sair'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _stop(self, ctx):
        await ctx.player.destroy()
        await ctx.send(ctx.t('commands.stop.stopped', {"author": ctx.author.name,
                                                       "emoji": self.disco.emoji["true"],
                                                       "channel": ctx.me.voice.channel}))

        if self.redis and ctx.author.voice:
            payload = {
                "type": "queue_end",
                "users": [member.id for member in ctx.author.voice.channel.members if not member.bot]
            }

            await self.redis.publish_json('activity', payload)

    @commands.command(name='volume', aliases=['vol', 'v'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _volume(self, ctx, vol: int):
        if not 0 < vol < 151:
            return await ctx.send(ctx.t('commands.volume.invalidValue', {
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        await ctx.player.set_volume(vol)
        await ctx.send(ctx.t('commands.volume.changed', {"author": ctx.author.name,
                                                         "emoji": self.disco.emoji["volume"],
                                                         "value": vol}))

    @commands.command(name='clear', aliases=['reset', 'limpar'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _clear(self, ctx):
        if not ctx.player.queue:
            return await ctx.send(ctx.t('commands.clear.alreadyEmpty', {
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        ctx.player.queue.clear()
        await ctx.send(ctx.t('commands.clear.cleaned', {"author": ctx.author.name,
                                                        "emoji": self.disco.emoji["alert"]}))

    @commands.command(name='pause', aliases=['pausar'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _pause(self, ctx):
        if not ctx.player.current:
            return await ctx.send(ctx.t('errors.notPlaying', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        if ctx.player.paused:
            await ctx.send(ctx.t('commands.pause.unpause', {"author": ctx.author.name,
                                                            "emoji": self.disco.emoji["pause"]}))
        else:
            await ctx.send(ctx.t('commands.pause.pause', {"author": ctx.author.name,
                                                          "emoji": self.disco.emoji["pause"]}))

        await ctx.player.set_pause(not ctx.player.paused)

        if self.redis:
            payload = {
                "type": "pause" if ctx.player.paused else "resume",
                "track": {
                    "position": ctx.player.position
                },
                "users": [member.id for member in ctx.author.voice.channel.members if not member.bot]
            }

            await self.redis.publish_json('activity', payload)

    @commands.command(name='remove', aliases=['r', 'remover', 'delete', 'del'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _remove(self, ctx, index: int):
        if not ctx.player.queue:
            return await ctx.send(ctx.t('errors.emptyQueue', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        try:
            track = ctx.player.queue.pop(index - 1)
        except IndexError:
            return await ctx.send(ctx.t('errors.invalidValue', {"author": ctx.author.name,
                                                                "emoji": self.disco.emoji["false"]}))

        await ctx.send(ctx.t('commands.remove.removed', {"author": ctx.author.name,
                                                         "emoji": self.disco.emoji["true"], "track": track}))

    @commands.command(name='playat', aliases=['pa', 'pularpara', 'skt', 'skipto'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def _play_at(self, ctx, index: int):
        player = ctx.player
        if not player.queue:
            return await ctx.send(ctx.t('errors.emptyQueue', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        try:
            player.queue = player.queue[index - 1:]
            track = player.queue.pop(0)
        except IndexError:
            return await ctx.send(ctx.t('errors.invalidValue', {"author": ctx.author.name,
                                                                "emoji": self.disco.emoji["false"]}))

        player.queue.insert(0, track)
        await player.stop()

    @commands.command(name='nowplaying', aliases=['np', 'tocandoagora', 'tocando', 'now'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _now_playing(self, ctx):
        player = self.disco.get_player(ctx.guild.id)
        if not player.current:
            return await ctx.send(ctx.t('errors.notPlaying', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        track = player.current
        bar = '─' * (width := 17)

        if track.is_stream:
            position = f'```{get_length(player.position)} %s LIVESTREAM```' % (bar[:-1] + '🔘')
        else:
            percentage = round(player.position / track.duration * width)
            position = f'```{get_length(player.position)} %s {get_length(track.duration)}```' \
                       % (bar[:percentage] + '🔘' + bar[percentage + 1:])

        em = discord.Embed(
            title=ctx.t('commands.nowplaying.nowPlaying'),
            colour=self.disco.color[0],
            description=f'[**{track}**]({track.uri})'
        ).add_field(
            name=ctx.t('commands.nowplaying.uploader'),
            value=track.author or ctx.t('commons.unknown')
        ).add_field(
            name=ctx.t('commands.nowplaying.addedBy'),
            value=track.requester.mention
        ).add_field(
            name=ctx.t('commands.nowplaying.position'),
            value=position,
            inline=False,
        ).set_thumbnail(
            url=track.thumb
        )

        await ctx.send(embed=em, delete_after=30)

    @commands.command(name='skip', aliases=['s', 'sk', 'skp'])
    @checks.is_voice_connected()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _skip(self, ctx):
        if not ctx.player.current:
            return await ctx.send(ctx.t('errors.notPlaying', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        track = ctx.player.current
        if track.requester.id == ctx.author.id:
            await ctx.send(ctx.t('commands.skip.skippedByRequester', {"track": track,
                                                                      "emoji": self.disco.emoji["alert"],
                                                                      "author": ctx.author.name}))

            return await ctx.player.stop()

        elif ctx.author.id in track.skip_votes:
            return await ctx.send(ctx.t('commands.skip.alreadyVoted', {
                "emoji": self.disco.emoji["false"], "author": ctx.author.name}))

        track.skip_votes.add(ctx.author.id)
        await ctx.send(ctx.t('commands.skip.voteAdded', {"author": ctx.author.name,
                                                         "emoji": self.disco.emoji["alert"],
                                                         "votes": len(track.skip_votes)}))

        if len(track.skip_votes) == 3:
            await ctx.send(ctx.t('commands.skip.skipped', {"track": track,
                                                           "emoji": self.disco.emoji["alert"]}))

            await ctx.player.stop()

    @commands.command(name='forceskip', aliases=['fskip', 'pularagora'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _force_skip(self, ctx):
        if not ctx.player.current:
            return await ctx.send(ctx.t('errors.notPlaying', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        await ctx.send(ctx.t('commands.forceskip.skipped', {"track": ctx.player.current,
                                                            "emoji": self.disco.emoji["alert"],
                                                            "author": ctx.author.name}))

        await ctx.player.stop()

    @commands.command(name='bassboost', aliases=['bass', 'boost', 'bb'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _bass_boost(self, ctx):
        if not ctx.player.current:
            return await ctx.send(ctx.t('errors.notPlaying', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        if ctx.player.bass_boost:
            await ctx.player.set_eq(Equalizer.boost())
            await ctx.send(ctx.t('commands.bassboost.disabled', {"emoji": self.disco.emoji["volume"],
                                                                 "author": ctx.author.name}))
        else:
            await ctx.player.set_eq(Equalizer.flat())
            await ctx.send(ctx.t('commands.bassboost.enabled', {"emoji": self.disco.emoji["volume"],
                                                                "author": ctx.author.name}))

        ctx.player.bass_boost = not ctx.player.bass_boost

    @commands.command(name='queue', aliases=['q', 'fila', 'lista'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _queue(self, ctx, page: int = 1):
        player = self.disco.get_player(ctx.guild.id)
        if not player.queue:
            return await ctx.send(ctx.t('errors.emptyQueue', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        length = get_length(sum(track.length for track in player.queue), True)

        per_page = 8
        pages = ceil(player.size / per_page)
        if not 0 < page <= pages:
            page = 1

        skip = (page - 1) * per_page
        current = player.current
        tracks = player.queue[skip:skip + per_page]

        txt = (ctx.t('commands.queue.currentTrack', {"track": current, "length": get_length(current.length)})
               if current else '') + '\n'.join(
            f'**`»`** `{i}` [**{t}**]({t.uri}) `[{get_length(t.length)}]` - {t.requester.mention}'
            for i, t in enumerate(tracks, skip + 1))

        em = discord.Embed(
            colour=self.disco.color[1],
            title=ctx.t('commands.queue.name'),
            description=txt
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url
        ).set_thumbnail(
            url=self.disco.user.avatar_url
        ).set_footer(
            text=ctx.t('commands.queue.details', {"length": length, "page": page, "pages": pages})
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='reverse', aliases=['rev', 'inverter'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _reverse(self, ctx):
        if not ctx.player.queue:
            return await ctx.send(ctx.t('errors.emptyQueue', {"author": ctx.author.name,
                                                              "emoji": self.disco.emoji["false"]}))

        ctx.player.queue.reverse()
        await ctx.send(ctx.t('commands.reverse.success', {"author": ctx.author.name,
                                                          "emoji": self.disco.emoji["shuffle"]}))

    @commands.command(name='seek', aliases=['jump'])
    @checks.staffer_or_dj_role()
    @checks.is_voice_connected()
    @commands.cooldown(2, 12, commands.BucketType.guild)
    async def _seek(self, ctx, position):
        if (current := ctx.player.current) is None:
            return await ctx.send(ctx.t('errors.notPlaying', {"emoji": self.disco.emoji["false"],
                                                              "author": ctx.author.name}))

        if current.is_stream:
            return await ctx.send(ctx.t('commands.seek.isStream', {"emoji": self.disco.emoji["false"],
                                                                   "author": ctx.author.name}))

        if not (position_ := SEEK_RX.match(position)):
            raise commands.errors.UserInputError

        hours, minutes, seconds = sorted(position_.groups(), key=lambda x: x is not None)
        to_skip = timedelta(hours=int(hours.lstrip('0') or 0) if hours else 0,
                            minutes=int(minutes.lstrip('0') or 0) if minutes else 0,
                            seconds=int(seconds.lstrip('0') or 0) if seconds else 0)

        if position.startswith('-'):
            position = max(ctx.player.position - to_skip.total_seconds() * 1000, 0)
        elif position.startswith('+'):
            position = min(ctx.player.position + to_skip.total_seconds() * 1000, current.length)
        else:
            position = min(to_skip.total_seconds() * 1000, current.length)

        await ctx.player.seek(position)
        await ctx.send(ctx.t('commands.seek.success', {"emoji": self.disco.emoji["true"],
                                                       "author": ctx.author.name,
                                                       "track": current.title,
                                                       "position": get_length(position)}))


def setup(disco):
    disco.add_cog(Music(disco))
