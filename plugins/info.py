from datetime import datetime

import discord
from discord.ext import commands
from humanize import naturalsize
from prettytable import PrettyTable

from utils import get_length, PATREON_DONATE_URL, SUPPORT_GUILD_INVITE_URL, BOT_INVITE_URL, BOT_LIST_VOTE_URL, \
    GITHUB_REPOSITORY_URL


class Information(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

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
        prefixes = [*([custom_prefix] if custom_prefix else self.disco.prefixes)]

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

    @commands.command(name='botinfo', aliases=['nodes', 'bi', 'statistics'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _bot_info(self, ctx):
        shard_ping = int(self.disco.shards[ctx.guild.shard_id].ws.latency * 1000)
        uptime = get_length((datetime.utcnow() - self.disco.started_at).total_seconds() * 1000, True)

        creator = self.disco.get_user(self.disco.owner_id)

        em = discord.Embed(
            colour=self.disco.color[0],
            title=ctx.t('commands.botinfo.statistics'),
            description=ctx.t('commands.botinfo.links', {
                "support": SUPPORT_GUILD_INVITE_URL,
                "invite": BOT_INVITE_URL,
                "donate": PATREON_DONATE_URL,
                "vote": BOT_LIST_VOTE_URL,
                "github": GITHUB_REPOSITORY_URL
            })
        ).set_author(
            name=ctx.me.name,
            icon_url=self.disco.user.avatar_url
        ).set_footer(
            text=ctx.t('commons.createdBy', {"creator": creator}),
            icon_url=creator.avatar_url
        ).set_thumbnail(
            url=self.disco.user.avatar_url
        ).add_field(
            name=ctx.t('commands.botinfo.generalInfoTitle'),
            value=ctx.t('commands.botinfo.generalInfoDescLeft', {
                "shard": ctx.guild.shard_id + 1,
                "shards": len(self.disco.shards),
                "ping": shard_ping,
                "servers": len(self.disco.guilds),
                "members": len(set(self.disco.get_all_members())),
                "players": len(self.disco.wavelink.players),
                "nodes": len(self.disco.wavelink.nodes)
            })
        ).add_field(
            name='\u200b',
            value=ctx.t('commands.botinfo.generalInfoDescRight', {
                "uptime": uptime,
                "messages": f'{self.disco.read_messages:,}',
                "commands": f'{self.disco.invoked_commands:,}',
                "played": f'{self.disco.played_tracks:,}'
            })
        )

        for identifier, node in self.disco.wavelink.nodes.items():
            stats = node.stats

            em.add_field(
                name=f'**LAVALINK NODE {identifier}**',
                value=ctx.t('commands.botinfo.nodeInfo', {
                    "status": '%s (%s)' % (ctx.t('commons.available' if node.is_available else 'commons.unavailable'),
                                           ctx.t('commons.connected' if node._websocket.is_connected else
                                                 'commons.disconnected')),
                    "region": node.region.title().replace("_", " "),
                    "uptime": get_length(stats.uptime, True),
                    "players": '%s/%s' % (stats.playing_players, stats.players),
                    "memoryUsed": naturalsize(stats.memory_used),
                    "cpuUsage": '%.1f' % (stats.lavalink_load * 100),
                    "cpuCores": stats.cpu_cores}),
                inline=False
            )

        await ctx.send(content=ctx.author.mention, embed=em)

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

    @commands.command(name='shards', aliases=['latencies'])
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _shards(self, ctx):
        table = PrettyTable(['SID', 'Ping', 'Uptime', 'Guilds', 'Members', 'Players', 'Last Update'])

        for shard in sorted(await self.disco.db.get_shards(), key=lambda s: s.id):
            now = datetime.utcnow()
            latency = f'{int(shard.latency * 1000)}ms' if shard.latency else 'Unknown'
            guilds = f'{shard.guilds:,}' if shard.guilds else 'Unknown'
            members = f'{shard.members:,}' if shard.members else 'Unknown'
            players = f'{shard.players:,}' if shard.players else '0'
            uptime = get_length((now - shard.launched_at).total_seconds() * 1000, True) \
                if shard.launched_at else 'Unknown'
            last_update = get_length((now - shard.last_update).total_seconds() * 1000, True) \
                if shard.last_update else 'Unknown'

            table.add_row([shard.id, latency, uptime, guilds, members, players, last_update])

        await ctx.send(f'```apache\n{table.get_string()}```')

    @commands.command(name='whatsmyprefix', hidden=True)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def _whats_my_prefix(self, ctx):
        command = ctx.t('commons.command')
        custom_prefix = ctx.gdb.options['prefix']
        prefixes = [*([custom_prefix] if custom_prefix else self.disco.prefixes)]

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
