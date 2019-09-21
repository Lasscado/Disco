from prettytable import PrettyTable
from discord.ext import commands
from humanize import naturalsize
from datetime import datetime
from utils import get_length, l

import discord

TRANSPARENT = 'https://cdn.discordapp.com/attachments/359388328233140239/471181808612933634/invisible.png'

class Information(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

    @commands.command(name='help', aliases=['ajuda', 'commands', 'cmds'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _help(self, ctx, command=None):
        if command:
            cmd = self.disco.get_command(command)
            if not cmd or cmd.hidden:
                return await ctx.send(l(ctx, 'commands.help.notFound', {"author": ctx.author.name,
                    "emoji": self.disco.emoji["false"]}))

            usage = l(ctx, f'commands.{cmd.name}.cmdUsage')

            em = discord.Embed(
                colour=self.disco.color[0],
                title=l(ctx, 'commands.help.commandName', {"command": cmd.name.title()})
            ).set_author(
                name=ctx.me.name,
                icon_url=ctx.me.avatar_url
            ).set_thumbnail(
                url=TRANSPARENT
            ).add_field(
                name=l(ctx, 'commands.help.description'),
                value=l(ctx, f'commands.{cmd.name}.cmdDescription') \
                    or l(ctx, 'commands.help.notSupplied')
            ).add_field(
                name=l(ctx, 'commands.help.usage'),
                value=f'{ctx.prefix}{cmd.name} {usage if usage else ""}'
            ).add_field(
                name=l(ctx, 'commands.help.aliases'),
                value=' | '.join([f'`{a}`' for a in cmd.aliases]) \
                    or l(ctx, 'commands.help.notDefined'),
                inline=False
            )

            return await ctx.send(content=ctx.author.mention, embed=em)

        prefixes = [ctx.prefix] if ctx._guild.data['options']['prefix'] \
            else self.disco.prefixes

        command = l(ctx, 'commons.command')
        prefixes = ' | '.join(f'`{prefix}<{command}>`' for prefix in prefixes)

        em = discord.Embed(
            timestap=ctx.message.created_at,
            colour=self.disco.color[0],
            description=l(ctx, 'commands.help.links', {
                "support": "https://discord.gg/qN5886E",
                "invite": "https://discobot.site",
                "donate": "https://patreon.com/discobot",
                "vote": "https://botsparadiscord.xyz/bots/discolite",
                "github": "https://github.com/Naegin/Disco",
                "prefixes": prefixes
            })
        ).set_author(
            name=ctx.me.name,
            icon_url=ctx.me.avatar_url
        ).set_thumbnail(
            url=ctx.me.avatar_url
        ).set_footer(
            text=l(ctx, 'commons.createdBy', {"creator": 'Naegin#0049'}),
            icon_url='https://cdn.naeg.in/i/naegin-avatar.gif'
        )

        for name, cog in self.disco.cogs.items():
            cmds = [c for c in cog.get_commands() if not c.hidden]
            value = ' | '.join([f'`{c}`' for c in cmds])

            if value:
                em.add_field(name=l(ctx, 'commands.help.categoryCommands', {"total": len(cmds),
                    "category": l(ctx, f'categories.{name.lower()}')}),
                    value=value)

        em.add_field(
            name='\u200b',
            value=l(ctx, 'commands.help.tip', {"command": f'{ctx.prefix}{ctx.invoked_with}'})
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='botinfo', aliases=['nodes', 'bi', 'statistics'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _bot_info(self, ctx):
        shard_ping = int(self.disco.shards[ctx.guild.shard_id].ws.latency * 1000)
        uptime = get_length((datetime.utcnow() - self.disco.started_at).total_seconds() * 1000,
            True)

        em = discord.Embed(
            colour=self.disco.color[0],
            title=l(ctx, 'commands.botinfo.statistics'),
            description=l(ctx, 'commands.botinfo.links', {
                "support": "https://discord.gg/qN5886E",
                "invite": "https://discobot.site",
                "donate": "https://patreon.com/discobot",
                "vote": "https://botsparadiscord.xyz/bots/discolite",
                "github": "https://github.com/Naegin/Disco"
            })
        ).set_author(
            name=ctx.me.name,
            icon_url=ctx.me.avatar_url
        ).set_footer(
            text=l(ctx, 'commons.createdBy', {"creator": "Naegin#0049"}),
            icon_url='https://cdn.naeg.in/i/naegin-avatar.gif'
        ).set_thumbnail(
            url=ctx.me.avatar_url
        ).add_field(
            name=l(ctx, 'commands.botinfo.generalInfoTitle'),
            value=l(ctx, 'commands.botinfo.generalInfoDescLeft', {
                "shard": ctx.guild.shard_id+1,
                "shards": len(self.disco.shards),
                "ping": shard_ping,
                "servers": len(self.disco.guilds),
                "members": len(set(self.disco.get_all_members())),
                "players": len(self.disco.wavelink.players),
                "nodes": len(self.disco.wavelink.nodes)
            })
        ).add_field(
            name='\u200b',
            value=l(ctx, 'commands.botinfo.generalInfoDescRight', {
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
                value=l(ctx, 'commands.botinfo.nodeInfo', {
                    "region": node.region.title().replace("_", " "),
                    "uptime": get_length(stats.uptime, True),
                    "stats": stats,
                    "memory": naturalsize(stats.memory_used)})
            )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='invite', aliases=['add', 'adicionar', 'convite', 'convidar'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _invite(self, ctx):
        em = discord.Embed(
            colour=self.disco.color[1],
            description=l(ctx, 'commands.invite.text', {"link": "https://discobot.site"})
        ).set_author(
            name=ctx.me.name,
            icon_url=ctx.me.avatar_url
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
        await ctx.send(l(ctx, 'commands.donate.text', {"emoji": self.disco.emoji["featured"],
            "link": "https://patreon.com/discobot"}))

    @commands.command(name='shards', aliases=['latencies'])
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _shards(self, ctx):
        table = PrettyTable(['Shard ID', 'Latency', 'Uptime', 'Guilds', 'Members', 'Last Update'])

        for shard in self.disco._shards.all():
            now = datetime.utcnow()
            latency = f'{int(shard.latency * 1000)}ms' if shard.latency else 'Unknown'
            guilds = f'{shard.guilds:,}' if shard.guilds else 'Unknown'
            members = f'{shard.members:,}' if shard.members else 'Unknown'
            uptime = get_length((now - shard.launched_at).total_seconds() * 1000, True) \
                if shard.launched_at else 'Unknown'
            last_update = get_length((now - shard.last_update).total_seconds() * 1000, True) \
                if shard.last_update else 'Unknown'

            table.add_row([shard.id, latency, uptime, guilds, members, last_update])

        await ctx.send(f'```{table.get_string()}```')

    @commands.command(name='whatsmyprefix')
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def _whats_my_prefix(self, ctx):
        command = l(ctx, 'commons.command')
        prefixes = [ctx.prefix] if ctx._guild.data['options']['prefix'] \
            else self.disco.prefixes

        await ctx.send(l(ctx, 'commands.whatsmyprefix.message', {"author": ctx.author.name,
            "prefixes": ' | '.join(f'`{prefix}<{command}>`' for prefix in prefixes),
            "emoji": self.disco.emoji["alert"]
        }))

def setup(disco):
    disco.add_cog(Information(disco))