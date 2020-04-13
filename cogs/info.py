from datetime import datetime, timedelta

import discord
from discord.ext import commands
from humanize import naturalsize
from prettytable import PrettyTable

from utils import get_length, PATREON_DONATE_URL, SUPPORT_GUILD_INVITE_URL, BOT_INVITE_URL, BOT_LIST_VOTE_URL, \
    GITHUB_REPOSITORY_URL


class Information(commands.Cog):
    def __init__(self, disco):
        self.disco = disco
        self._command_usage_cache = None

    @commands.command(name='help', aliases=['ajuda', 'commands', 'cmds'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _help(self, ctx, *, command_=None):
        if command_:
            cmd = self.disco.get_command(command_)
            if not cmd or cmd.hidden:
                return await ctx.send(ctx.t('commands.help.notFound', {"author": ctx.author.name,
                                                                       "emoji": self.disco.emoji["false"]}))

            qualified_name = cmd.qualified_name
            metadata = ctx.t(f'commands.{".".join(cmd.qualified_name.split(" "))}.meta') or {}
            description = metadata.get('description', ctx.t('commands.help.notSupplied'))
            usage = metadata.get('usage')

            em = discord.Embed(
                colour=self.disco.color[0],
                title=ctx.t('commands.help.commandName', {"command": cmd.name.title()}),
            ).set_author(
                name=ctx.me.name,
                icon_url=self.disco.user.avatar_url
            ).set_thumbnail(
                url=self.disco.user.avatar_url
            ).add_field(
                name=ctx.t('commands.help.description', {"emoji": self.disco.emoji["list"]}),
                value=description,
                inline=False
            ).add_field(
                name=ctx.t('commands.help.usage', {"emoji": self.disco.emoji["check"]}),
                value=f'`{ctx.prefix}{qualified_name}{" " + usage if usage else ""}`'
            ).add_field(
                name=ctx.t('commands.help.aliases', {"emoji": self.disco.emoji["dots"],
                                                     "total": len(cmd.aliases)}),
                value=' | '.join([f'`{a}`' for a in cmd.aliases]) or ctx.t('commands.help.notDefined'),
                inline=False
            )

            if hasattr(cmd, 'commands'):
                em.add_field(
                    name=ctx.t('commands.help.subCommands', {"emoji": self.disco.emoji["dots"],
                                                             "total": len(cmd.commands)}),
                    value=' | '.join([f'`{c.name}`' for c in cmd.commands])
                ).add_field(
                    name='\u200b',
                    value=ctx.t('commands.help.subCommandsTip', {"invoked": ctx.prefix + (ctx.invoked_with
                                                                                          if ctx.command.name == 'help'
                                                                                          else 'help'),
                                                                 "command": cmd.name}),
                    inline=False
                )

            em.add_field(
                name='\u200b',
                value=ctx.t('commands.help.support', {"link": SUPPORT_GUILD_INVITE_URL})
            )

            return await ctx.send(content=ctx.author.mention, embed=em)

        custom_prefix = ctx.gdb.options['prefix']
        prefixes = [*([custom_prefix] if custom_prefix else self.disco.default_prefixes)]

        command = ctx.t('commons.command')

        creator = self.disco.get_user(self.disco.owner_id)

        em = discord.Embed(
            timestap=ctx.message.created_at,
            colour=self.disco.color[0],
            description=ctx.t('commands.help.links', {
                "support": SUPPORT_GUILD_INVITE_URL,
                "invite": BOT_INVITE_URL,
                "donate": PATREON_DONATE_URL,
                "vote": BOT_LIST_VOTE_URL,
                "github": GITHUB_REPOSITORY_URL,
                "prefixes": ' | '.join(f'`{prefix}<{command}>`' for prefix in prefixes)
            })
        ).set_author(
            name=ctx.me.name,
            icon_url=self.disco.user.avatar_url
        ).set_thumbnail(
            url=self.disco.user.avatar_url
        ).set_footer(
            text=ctx.t('commons.createdBy', {"creator": creator}),
            icon_url=creator.avatar_url
        )

        for name, cog in sorted(self.disco.cogs.items(), key=lambda c: c[0] == 'Music', reverse=True):
            cmds = [c for c in cog.get_commands() if not c.hidden]
            value = ' | '.join(f'`{c}`' for c in cmds)

            if value:
                em.add_field(name=ctx.t('commands.help.categoryCommands', {"total": len(cmds),
                                                                           "category": ctx.t(
                                                                               f'categories.{name.lower()}'),
                                                                           "emoji": self.disco.emoji[
                                                                               "category" + name]}),
                             value=value,
                             inline=False)

        em.add_field(
            name='\u200b',
            value=ctx.t('commands.help.tip', {"command": f'{ctx.prefix}{ctx.invoked_with}'})
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.group(name='stats', aliases=['botinfo', 'data', 'statistics', 'bi'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _stats(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.disco.get_command('help'), command_='stats')

    @_stats.command(name='commands', aliases=['cmds', 'cmd', 'command'])
    async def _stats_command_usage(self, ctx):
        if not (data := self._command_usage_cache) or datetime.utcnow() > data['last_update'] + timedelta(minutes=5):
            public_commands = [c.qualified_name for c in self.disco.commands
                               if not c.hidden and c.cog.qualified_name != 'Owner']

            dt_24h = datetime.utcnow() - timedelta(hours=24)
            dt_1w = datetime.utcnow() - timedelta(weeks=1)
            dt_1m = datetime.utcnow() - timedelta(days=30)

            last_24_hours = [(c, await self.disco.db.get_total_command_usage(c, after=dt_24h)) for c in public_commands]
            last_week = [(c, await self.disco.db.get_total_command_usage(c, after=dt_1w)) for c in public_commands]
            last_month = [(c, await self.disco.db.get_total_command_usage(c, after=dt_1m)) for c in public_commands]
            lifetime = [(c, await self.disco.db.get_total_command_usage(c)) for c in public_commands]

            last_24_hours.sort(key=lambda c: c[1], reverse=True)
            last_week.sort(key=lambda c: c[1], reverse=True)
            last_month.sort(key=lambda c: c[1], reverse=True)
            lifetime.sort(key=lambda c: c[1], reverse=True)

            self._command_usage_cache = data = {"last_update": datetime.utcnow(),
                                                "last_24_hours": last_24_hours,
                                                "last_week": last_week,
                                                "last_month": last_month,
                                                "lifetime": lifetime}

        limit = 8
        uses = ctx.t('commons.uses')

        self._command_usage_embed = em = discord.Embed(
            title=ctx.t('commands.stats.commands.title'),
            colour=self.disco.color[0],
            timestamp=data['last_update']
        ).set_author(
            name=self.disco.user.name,
            icon_url=self.disco.user.avatar_url
        ).set_footer(
            text=ctx.t('commands.stats.commands.lastUpdate')
        ).set_thumbnail(
            url=self.disco.user.avatar_url
        ).add_field(
            name=ctx.t('commands.stats.commands.last24Hours', {"total": sum(c[1] for c in data['last_24_hours'])}),
            value='\n'.join(f'**`{i}`**. **{c[0]}** ({c[1]} {uses})'
                            for i, c in enumerate(data['last_24_hours'][:limit], 1))
        ).add_field(
            name='\u200b',
            value='\u200b'
        ).add_field(
            name=ctx.t('commands.stats.commands.lastWeek', {"total": sum(c[1] for c in data['last_week'])}),
            value='\n'.join(f'**`{i}`**. **{c[0]}** ({c[1]} {uses})'
                            for i, c in enumerate(data['last_week'][:limit], 1))
        ).add_field(
            name=ctx.t('commands.stats.commands.lastMonth', {"total": sum(c[1] for c in data['last_month'])}),
            value='\n'.join(f'**`{i}`**. **{c[0]}** ({c[1]} {uses})'
                            for i, c in enumerate(data['last_month'][:limit], 1)),
        ).add_field(
            name='\u200b',
            value='\u200b'
        ).add_field(
            name=ctx.t('commands.stats.commands.lifetime', {"total": sum(c[1] for c in data['lifetime'])}),
            value='\n'.join(f'**`{i}`**. **{c[0]}** ({c[1]} {uses})'
                            for i, c in enumerate(data['lifetime'][:limit], 1))
        )

        await ctx.send(ctx.author.mention, embed=em)

    @_stats.command(name='lavalink', aliases=['nodes', 'lava', 'music', 'audio'])
    async def _stats_lavalink(self, ctx):
        em = discord.Embed(
            title='Lavalink Nodes',
            colour=self.disco.color[0],
            timestamp=datetime.utcnow()
        ).set_author(
            name=self.disco.user.name,
            icon_url=self.disco.user.avatar_url
        ).set_footer(
            text=ctx.t('commands.stats.lavalink.playedTracks', {"total": f"{self.disco.played_tracks:,}"})
        )

        for i, node in enumerate(self.disco.wavelink.nodes.copy().values(), 1):
            if i % 2 == 0:
                em.add_field(name='\u200b', value='\u200b')

            stats = node.stats

            em.add_field(
                name=f'**{node.identifier}**',
                value=ctx.t('commands.stats.lavalink.nodeInfo', {
                    "status": '%s (%s)' % (ctx.t('commons.available' if node.is_available else 'commons.unavailable'),
                                           ctx.t('commons.connected' if node._websocket.is_connected else
                                                 'commons.disconnected')),
                    "region": node.region.title().replace("_", " "),
                    "uptime": get_length(stats.uptime, True),
                    "players": '%s/%s' % (stats.playing_players, stats.players),
                    "memoryUsed": naturalsize(stats.memory_used),
                    "cpuUsage": '%.1f' % (stats.lavalink_load * 100),
                    "cpuCores": stats.cpu_cores})
            )

        await ctx.send(ctx.author.mention, embed=em)

    @_stats.command(name='events', aliases=['socket'])
    async def _stats_socket_responses(self, ctx):
        events = sorted(self.disco.socket_responses.copy().items(), key=lambda x: len(x[0] or 'UNKNOWN'), reverse=True)

        space_1 = len(events[0][0]) + 5
        space_2 = len(f'{sorted(events, key=lambda x: x[1], reverse=True)[0][1]:,}') + 5

        seconds = (datetime.utcnow() - self.disco.started_at).total_seconds()

        lines = ['%s: %s : %.4f/s' % ((event_type or 'UNKNOWN').ljust(space_1),
                                      f'{received:,}'.ljust(space_2),
                                      received / seconds)
                 for event_type, received in events]

        space_3 = len(lines[0]) + 8

        await ctx.send('```apache\n_ WEBSOCKET RESPONSES FROM DISCORD (Since %s)\n%s\n%s\n```' % (self.disco.started_at,
                                                                                                  '-' * space_3,
                                                                                                  '\n'.join(lines[:20])))

        if len(lines) > 20:
            await ctx.send('```apache\n%s\n```' % '\n'.join(lines[20:]))

    @_stats.command(name='shards', aliases=['latencies'])
    async def _stats_shards(self, ctx):
        table = PrettyTable(['SID', 'Ping', 'Uptime', 'Guilds', 'Members', 'Players', 'Last Update'])

        shards = sorted(await self.disco.db.get_shards(), key=lambda s: s.id)
        now = datetime.utcnow()

        for shard in shards:
            shard_id = f'{shard.id}*' if shard.id == ctx.guild.shard_id else shard.id
            latency = f'{int(shard.latency * 1000)}ms' if shard.latency else 'Unknown'
            guilds = f'{shard.guilds:,}' if shard.guilds else 'Unknown'
            members = f'{shard.members:,}' if shard.members else 'Unknown'
            players = f'{shard.players:,}'
            uptime = get_length((now - shard.launched_at).total_seconds() * 1000, True) \
                if shard.launched_at else 'Unknown'
            last_update = get_length((now - shard.last_update).total_seconds() * 1000, True) \
                if shard.last_update else 'Unknown'

            table.add_row([shard_id, latency, uptime, guilds, members, players, last_update])

        ping_average = '%sms' % int(sum((s.latency * 1000 or 0) for s in shards) / len(shards))
        total_guilds = f'{sum(s.guilds for s in shards):,}'
        total_members = f'{sum(s.members for s in shards):,}'
        total_players = f'{sum(s.players for s in shards):,}'

        table.add_row(['-', '-', '-', '-', '-', '-', '-'])
        table.add_row(['Total', ping_average, '', total_guilds, total_members, total_players, ''])

        await ctx.send(f'```apache\n{table.get_string()}```')

    @commands.command(name='invite', aliases=['add', 'adicionar', 'convite', 'convidar'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _invite(self, ctx):
        em = discord.Embed(
            colour=self.disco.color[1],
            description=ctx.t('commands.invite.text', {"link": BOT_INVITE_URL})
        ).set_author(
            name=ctx.me.name,
            icon_url=self.disco.user.avatar_url
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='ping', aliases=['latency'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _ping(self, ctx):
        ping = int(self.disco.shards[ctx.guild.shard_id].ws.latency * 1000)
        await ctx.send(f'{self.disco.emoji["wireless"]} **Ping**: **`{ping}ms`**')

    @commands.command(name='donate', aliases=['donation', 'doar'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _donate(self, ctx):
        await ctx.send(ctx.t('commands.donate.text', {"emoji": self.disco.emoji["featured"],
                                                      "link": PATREON_DONATE_URL}))

    @commands.command(name='whatsmyprefix', hidden=True)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def _whats_my_prefix(self, ctx):
        command = ctx.t('commons.command')
        custom_prefix = ctx.gdb.options['prefix']
        prefixes = [*([custom_prefix] if custom_prefix else self.disco.default_prefixes)]

        await ctx.send(ctx.t('commands.whatsmyprefix.message', {"author": ctx.author.name,
                                                                "prefixes": ' | '.join(
                                                                    f'`{prefix}<{command}>`' for prefix in prefixes),
                                                                "emoji": self.disco.emoji["alert"]
                                                                }))

    @commands.command(name='serversettings', aliases=['settings', 'configs'])
    @commands.cooldown(1, 8, commands.BucketType.channel)
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(embed_links=True)
    async def _settings(self, ctx):
        not_defined = ctx.t('commands.serversettings.notDefined')
        options = ctx.gdb.options

        em = discord.Embed(
            colour=self.disco.color[0],
            title=ctx.t('commands.serversettings.title')
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url
        ).add_field(
            name=ctx.t('commands.serversettings.customPrefix'),
            value=f'`{options["prefix"] or not_defined}`'
        ).add_field(
            name=ctx.t('commands.serversettings.djRole'),
            value=f'`{ctx.guild.get_role(options["dj_role"]) or not_defined}`'
        ).add_field(
            name=ctx.t('commands.serversettings.modRole'),
            value=f'`{ctx.guild.get_role(options["mod_role"]) or not_defined}`'
        ).add_field(
            name=ctx.t('commands.serversettings.modLogsChannel'),
            value=f'`{ctx.guild.get_channel(options["mod_logs_channel"]) or not_defined}`'
        ).add_field(
            name=ctx.t('commands.serversettings.botChannel'),
            value=f'`{ctx.guild.get_channel(options["bot_channel"]) or not_defined}`'
        ).add_field(
            name=ctx.t('commands.serversettings.defaultVolume'),
            value=f'`{options["default_volume"]}%`' if options['default_volume'] else f'`{not_defined}`'
        ).add_field(
            name=ctx.t('commands.serversettings.locale'),
            value=f'`{options["locale"]}`'
        ).add_field(
            name=ctx.t('commands.serversettings.localBans'),
            value=f'`{len(options["banned_members"])}`'
        ).add_field(
            name=ctx.t('commands.serversettings.disabledRoles'),
            value=f'`{len(options["disabled_roles"])}`'
        ).add_field(
            name=ctx.t('commands.serversettings.disabledChannels'),
            value=f'`{len(options["disabled_channels"])}`'
        ).add_field(
            name=ctx.t('commands.serversettings.disabledCommands'),
            value=f'`{len(options["disabled_commands"])}`'
        )

        await ctx.send(embed=em)


def setup(disco):
    disco.add_cog(Information(disco))
