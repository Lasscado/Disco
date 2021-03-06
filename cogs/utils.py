from asyncio import TimeoutError as TimeoutException
from datetime import timedelta
from os import environ

import discord
import genius
import kitsu
from babel.dates import format_date, format_timedelta
from discord.ext import commands
from wavelink.errors import ZeroConnectedNodes

from utils import TRANSPARENT_IMAGE_URL


class Utils(commands.Cog):
    def __init__(self, disco):
        self.disco = disco
        self.genius = genius.Client(environ['GENIUS_API_TOKEN'])
        self.kitsu = kitsu.Client()

    @commands.command(name='avatar', aliases=['av', 'pfp', 'picture'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def _avatar(self, ctx, *, member: discord.Member = None):
        if not member:
            member = ctx.author

        em = discord.Embed(
            colour=member.colour if member.colour.value else self.disco.color[0],
            description=ctx.t('commands.avatar.clickToDownload', {"url": member.avatar_url})
        ).set_author(
            name=ctx.t('commands.avatar.memberAvatar', {"member": member}),
            icon_url=member.avatar_url
        ).set_image(
            url=member.avatar_url
        ).set_footer(
            text=str(ctx.author)
        )

        await ctx.send(embed=em)

    @commands.command(name='lyrics', aliases=['ly'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _lyrics(self, ctx, *, query=None):
        thumb = self.disco.user.avatar_url

        if not query:
            if activities := [a for a in ctx.author.activities if isinstance(a, discord.Spotify)]:
                to_search = '{0.artists[0]} {0.title}'.format(track := activities[0])
                thumb = track.album_cover_url
            elif (ctx.author.voice and ctx.me.voice) and ctx.author.voice.channel == ctx.me.voice.channel:
                if playing := self.disco.get_player(ctx.guild.id).current:
                    to_search = playing.title
                else:
                    return await ctx.send(ctx.t('commands.lyrics.notPlaying', {"emoji": self.disco.emoji['false'],
                                                                               "author": ctx.author.name}))
            else:
                raise commands.UserInputError

            songs = await self.genius.search(to_search)
            if not songs:
                return await ctx.send(ctx.t('commands.lyrics.currentNotFound', {"emoji": self.disco.emoji['false'],
                                                                                "author": ctx.author.name}))
        else:
            songs = await self.genius.search(query)
            if not songs:
                return await ctx.send(ctx.t('commands.lyrics.notFound', {"emoji": self.disco.emoji['false'],
                                                                         "author": ctx.author.name}))

        options = '\n'.join(f'**`»`** `{i}` [**{song.artist} - {song}**]({song.url})'
                            for i, song in enumerate(songs, 1))

        cancel = ctx.t('commons.exit').lower()

        em = discord.Embed(
            colour=self.disco.color[0],
            title=ctx.t('commands.lyrics.chooseOne'),
            description=options
        ).set_author(
            name=ctx.t('commands.lyrics.searchResults') + ('' if query else ' '
                                                                            + ctx.t('commands.lyrics.listeningOnSpotify'
                                                                                    if 'activities' in locals()
                                                                                       and activities
                                                                                    else 'commands.lyrics.nowPlaying')),
            icon_url=ctx.guild.icon_url
        ).set_thumbnail(
            url=thumb
        ).set_footer(
            text=ctx.t('commands.lyrics.typeToCancel', {"value": cancel})
        )

        q = await ctx.send(content=ctx.author.mention, embed=em)

        def check(m):
            return m.channel.id == q.channel.id and m.author.id == ctx.author.id and m.content \
                   and (m.content.isdecimal() and 0 < int(m.content) <= len(songs) or m.content.lower() == cancel)

        try:
            a = await self.disco.wait_for('message', timeout=120, check=check)
        except TimeoutException:
            a = None

        if not a or a.content.lower() == cancel:
            return await q.delete()

        song = songs[int(a.content) - 1]

        lyrics = await self.genius.get_lyrics(song)
        if not lyrics:
            return await ctx.send(ctx.t('commands.lyrics.lyricsNotFound', {"emoji": self.disco.emoji['false'],
                                                                           "author": ctx.author.name}))

        view_more = ctx.t("commands.lyrics.viewMore", {"url": song.url})
        if len(lyrics) > 2048:
            lyrics = lyrics[:2048 - len(view_more)] + view_more

        em = discord.Embed(
            colour=self.disco.color[1],
            title=f'{song.artist} - {song}',
            description=lyrics,
            url=song.url
        ).set_thumbnail(
            url=song.image_url
        ).set_author(
            name=ctx.t('commands.lyrics.songLyrics'),
            icon_url=self.disco.user.avatar_url
        ).set_footer(
            text=str(ctx.author)
        )

        await q.edit(content=None, embed=em)

    @commands.command(name='anime')
    @commands.cooldown(1, 8, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def _anime(self, ctx, *, query):
        entries = await self.kitsu.search('anime', query)
        if not entries:
            return await ctx.send(ctx.t('commands.anime.notFound', {"emoji": self.disco.emoji["false"],
                                                                    "author": ctx.author.name}))

        replace_subtypes = ['movie', 'music', 'special']
        for anime in entries:
            if anime.subtype in replace_subtypes:
                anime.subtype = ctx.t('commons.' + anime.subtype)

        options = '\n'.join(f'**`»` `{i}` [{anime}]({anime.url})** ({anime.subtype})'
                            for i, anime in enumerate(entries, 1))
        cancel = ctx.t('commons.exit').lower()

        em = discord.Embed(
            color=self.disco.color[0],
            title=ctx.t('commands.anime.chooseOne'),
            description=options,
        ).set_author(
            name=ctx.t('commands.anime.searchResults'),
            icon_url=ctx.author.avatar_url
        ).set_thumbnail(
            url=self.disco.user.avatar_url
        ).set_footer(
            text=ctx.t('commands.anime.typeToCancel', {"value": cancel})
        )

        q = await ctx.send(content=ctx.author.mention, embed=em)

        def check(m):
            return m.channel.id == q.channel.id and m.author.id == ctx.author.id \
                   and (m.content.isdecimal() and 0 < int(m.content) <= len(entries) or m.content.lower() == cancel)

        try:
            a = await self.disco.wait_for('message', timeout=120, check=check)
        except TimeoutException:
            a = None

        if a is None or a.content.lower() == cancel:
            return await q.delete()

        anime = entries[int(a.content) - 1]
        if anime.nsfw and not ctx.channel.nsfw:
            return await q.edit(content=ctx.t('commands.anime.choiceIsNsfw', {"emoji": self.disco.emoji["false"],
                                                                              "author": ctx.author.name}),
                                embed=None)

        categories = await self.kitsu.fetch_media_categories(anime)
        categories.sort(key=lambda item: item.title)
        streaming_links = await self.kitsu.fetch_anime_streaming_links(anime)
        streaming_links.sort(key=lambda item: item.title)

        full_synopsis = ctx.t('commands.anime.readFullSynopsis', {"url": anime.url})
        if len(anime.synopsis) > 2048:
            anime.synopsis = anime.synopsis[:2048 - len(full_synopsis)] + full_synopsis

        unknown = ctx.t('commons.unknown')
        locale = ctx.gdb.options['locale']
        started_at = format_date(anime.started_at, format='short', locale=locale) if anime.started_at else unknown
        ended_at = format_date(anime.ended_at, format='short', locale=locale) if anime.ended_at else unknown
        total_length = ctx.t('commands.anime.totalLength', {"length": format_timedelta(
            timedelta(minutes=anime.episode_count * anime.episode_length), locale=locale)}) \
            if anime.episode_count and anime.episode_length else ''

        em.title = f'**{anime}**'
        em.description = anime.synopsis or ctx.t('commands.anime.noSynopsis')
        em.url = anime.url
        em.set_author(
            name='Anime',
            icon_url=self.disco.user.avatar_url
        ).set_thumbnail(
            url=anime.poster_image_url
        ).set_footer(
            text=str(ctx.author)
        ).add_field(
            name=ctx.t('commons.status'),
            value=ctx.t('commands.anime.status', {"status": ctx.t('commands.anime.' + anime.status),
                                                  "subtype": anime.subtype}) + (ctx.t('commands.anime.episodes',
                                                                                      {"episodes": anime.episode_count})
                                                                                if anime.episode_count else '')
        ).add_field(
            name=ctx.t('commons.aired'),
            value=f'**{ctx.t("commons.start")}**: {started_at}\n**{ctx.t("commons.end")}**: {ended_at}'
        ).add_field(
            name=ctx.t('commons.length'),
            value=total_length + (ctx.t('commands.anime.episodesLength', {"length": anime.episode_length})
                                  if anime.episode_length else unknown)
        ).add_field(
            name=ctx.t('commons.ranking'),
            value=ctx.t('commands.anime.ranking', {"popularity": anime.popularity_rank or unknown,
                                                   "rating": anime.rating_rank or unknown})
        ).add_field(
            name=ctx.t('commands.anime.watchOnline'),
            value=('\n'.join(f'[{streamer}]({streamer.url})' for streamer in streaming_links)
                   if streaming_links else ctx.t('commands.anime.noLinksFound'))
        ).add_field(
            name=ctx.t('commons.averageRating'),
            value=f'{(float(anime.average_rating) / 10):.2f}/10' if anime.average_rating else unknown
        ).add_field(
            name=ctx.t('commons.categories'),
            value=', '.join(
                f'[{ctx.t("categories.kitsu" + category.title.replace(" ", "")) or category}]({category.url})'
                for category in categories) if categories else unknown,
            inline=False
        ).add_field(
            name='\u200b',
            value=f'[**Kitsu**]({anime.url})'
                  + (f' | [**Trailer**](https://youtube.com/watch?v={anime.youtube_video_id})'
                     if anime.youtube_video_id else '')
        )

        await q.edit(content=None, embed=em)

    @commands.command(name='manga')
    @commands.cooldown(1, 8, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def _manga(self, ctx, *, query):
        entries = await self.kitsu.search('manga', query)
        if not entries:
            return await ctx.send(ctx.t('commands.manga.notFound', {"emoji": self.disco.emoji["false"],
                                                                    "author": ctx.author.name}))

        replace_subtypes = ['manga', 'oneshot', 'oel']
        for manga in entries:
            manga.subtype = ctx.t('commands.manga.' + manga.subtype) \
                if manga.subtype in replace_subtypes else manga.subtype.title()

        options = '\n'.join(f'**`»` `{i}` [{manga}]({manga.url})** ({manga.subtype})'
                            for i, manga in enumerate(entries, 1))
        cancel = ctx.t('commons.exit').lower()

        em = discord.Embed(
            color=self.disco.color[0],
            title=ctx.t('commands.manga.chooseOne'),
            description=options,
        ).set_author(
            name=ctx.t('commands.manga.searchResults'),
            icon_url=ctx.author.avatar_url
        ).set_thumbnail(
            url=self.disco.user.avatar_url
        ).set_footer(
            text=ctx.t('commands.manga.typeToCancel', {"value": cancel})
        )

        q = await ctx.send(content=ctx.author.mention, embed=em)

        def check(m):
            return m.channel.id == q.channel.id and m.author.id == ctx.author.id \
                   and (m.content.isdecimal() and 0 < int(m.content) <= len(entries) or m.content.lower() == cancel)

        try:
            a = await self.disco.wait_for('message', timeout=120, check=check)
        except TimeoutException:
            a = None

        if a is None or a.content.lower() == cancel:
            return await q.delete()

        manga = entries[int(a.content) - 1]
        if manga.subtype == 'Doujin' and not ctx.channel.nsfw:
            return await q.edit(content=ctx.t('commands.manga.choiceIsNsfw', {"emoji": self.disco.emoji["false"],
                                                                              "author": ctx.author.name}),
                                embed=None)

        categories = await self.kitsu.fetch_media_categories(manga)
        categories.sort(key=lambda item: item.title)

        full_synopsis = ctx.t('commands.anime.readFullSynopsis', {"url": manga.url})
        if len(manga.synopsis) > 2048:
            manga.synopsis = manga.synopsis[:2048 - len(full_synopsis)] + full_synopsis

        unknown = ctx.t('commons.unknown')
        locale = ctx.gdb.options['locale']
        started_at = format_date(manga.started_at, format='short', locale=locale) if manga.started_at else unknown
        ended_at = format_date(manga.ended_at, format='short', locale=locale) if manga.ended_at else unknown
        volume_count = ctx.t('commands.manga.volumes', {"volumes": manga.volume_count}) if manga.volume_count else ''
        chapter_count = ctx.t('commands.manga.chapters', {"chapters": manga.chapter_count}) \
            if manga.chapter_count else ''

        em.title = f'**{manga}**'
        em.description = manga.synopsis or ctx.t('commands.anime.noSynopsis')
        em.url = manga.url
        em.set_author(
            name=ctx.t('commands.manga.manga'),
            icon_url=self.disco.user.avatar_url
        ).set_thumbnail(
            url=manga.poster_image_url
        ).set_footer(
            text=str(ctx.author)
        ).add_field(
            name=ctx.t('commons.status'),
            value=ctx.t('commands.anime.status', {"status": ctx.t('commands.anime.' + manga.status),
                                                  "subtype": manga.subtype})
        ).add_field(
            name=ctx.t('commons.aired'),
            value=f'**{ctx.t("commons.start")}**: {started_at}\n**{ctx.t("commons.end")}**: {ended_at}'
        ).add_field(
            name=ctx.t('commands.manga.material'),
            value=volume_count + chapter_count or unknown
        ).add_field(
            name=ctx.t('commons.ranking'),
            value=ctx.t('commands.anime.ranking', {"popularity": manga.popularity_rank or unknown,
                                                   "rating": manga.rating_rank or unknown})
        ).add_field(
            name=ctx.t('commands.manga.serialization'),
            value=manga.serialization or unknown
        ).add_field(
            name=ctx.t('commons.averageRating'),
            value=f'{(float(manga.average_rating) / 10):.2f}/10' if manga.average_rating else unknown
        ).add_field(
            name=ctx.t('commons.categories'),
            value=', '.join(
                f'[{ctx.t("categories.kitsu" + category.title.replace(" ", "")) or category}]({category.url})'
                for category in categories) if categories else unknown,
            inline=False
        ).add_field(
            name='\u200b',
            value=f'[**Kitsu**]({manga.url})'
        )

        await q.edit(content=None, embed=em)

    @commands.command(name='youtube', aliases=['yt'])
    @commands.cooldown(3, 10, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def _youtube(self, ctx, *, query):
        try:
            results = await self.disco.wavelink.get_tracks(f'ytsearch:{query}')
        except ZeroConnectedNodes:
            return await ctx.send(ctx.t('commands.youtube.zeroNodes', {"emoji": self.disco.emoji["false"],
                                                                       "author": ctx.author.name}))

        if not results:
            return await ctx.send(ctx.t('commands.youtube.noResults', {"emoji": self.disco.emoji["false"],
                                                                       "author": ctx.author.name}))

        await ctx.send(results[0].uri)

    @commands.command(name='selfassignableroles', aliases=['sar'])
    @commands.cooldown(1, 8, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True, manage_roles=True)
    async def _self_assignable_roles(self, ctx, *, role: discord.Role = None):
        if role is None:
            self_assignable_roles = await self.disco.db.get_self_assignable_roles(ctx.guild.id)
            valid_roles = []

            for role_id in self_assignable_roles.roles:
                if role := ctx.guild.get_role(role_id):
                    valid_roles.append(role)

            em = discord.Embed(
                colour=self.disco.color[0],
                title=ctx.t('commands.selfassignableroles.assignableRoles'),
                description=('\n'.join(f'**`{i}`**. {r.mention}' for i, r in enumerate(valid_roles, 1))
                             or ctx.t('commands.selfassignableroles.noRoles'))
            ).set_author(
                name=ctx.guild.name,
                icon_url=ctx.guild.icon_url
            ).set_thumbnail(
                url=TRANSPARENT_IMAGE_URL
            ).set_footer(
                text=ctx.t('commands.selfassignableroles.tip', {"invocation": ctx.prefix + ctx.invoked_with})
            )

            return await ctx.send(ctx.author.mention, embed=em)

        if role >= ctx.me.top_role:
            return await ctx.send(ctx.t('commands.selfassignableroles.roleIsHigherThanMine',
                                        {"emoji": self.disco.emoji["false"],
                                         "author": ctx.author.name,
                                         "role": role.name}))

        self_roles = await self.disco.db.get_self_assignable_roles(ctx.guild.id)

        if role.id not in self_roles.roles:
            return await ctx.send(ctx.t('commands.selfassignableroles.invalidRole', {"emoji": self.disco.emoji["false"],
                                                                                     "author": ctx.author.name,
                                                                                     "role": role.name}))

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role, reason='Disco Self Assignable Role')
            return await ctx.send(ctx.t('commands.selfassignableroles.removed', {"emoji": self.disco.emoji["true"],
                                                                                 "author": ctx.author.name,
                                                                                 "role": role.name}))

        await ctx.author.add_roles(role, reason='Disco Self Assignable Role')
        await ctx.send(ctx.t('commands.selfassignableroles.added', {"emoji": self.disco.emoji["true"],
                                                                    "author": ctx.author.name,
                                                                    "role": role.name}))


def setup(disco):
    disco.add_cog(Utils(disco))
