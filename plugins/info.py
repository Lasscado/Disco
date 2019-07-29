from discord.ext import commands
from humanize import naturalsize
from utils import get_length
from utils import l

import discord

TRANSPARENT = 'https://cdn.discordapp.com/attachments/359388328233140239/471181808612933634/invisible.png'

class Info(commands.Cog, name='Informações'):
    def __init__(self, lite):
        self.lite = lite

    @commands.command(name='help', aliases=['ajuda', 'commands', 'cmds'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _help(self, ctx, command=None):
        if command:
            cmd = self.lite.get_command(command)
            if not cmd or cmd.hidden:
                return await ctx.send(l(ctx, 'commands.help.notFound') % (
                    self.lite.emoji["false"], ctx.author.name))

            usage = l(ctx, f'commands.{cmd.name}.cmdUsage')

            em = discord.Embed(
                colour=self.lite.color[0],
                title=l(ctx, 'commands.help.commandName') % cmd.name.title()
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
                value=', '.join([f'`{a}`' for a in cmd.aliases]) \
                    or l(ctx, 'commands.help.notDefined'),
                inline=False
            )

            return await ctx.send(content=ctx.author.mention, embed=em)

        em = discord.Embed(
            timestap=ctx.message.created_at,
            colour=self.lite.color[0],
            description=l(ctx, 'commands.help.links') % ('https://discord.gg/qN5886E',
                                                        'https://lite.discobot.site',
                                                        'https://botsparadiscord.xyz/bots/discolite',
                                                        'https://github.com/Naegin/DiscoLite')
        ).set_author(
            name=ctx.me.name,
            icon_url=ctx.me.avatar_url
        ).set_thumbnail(
            url=ctx.me.avatar_url
        ).set_footer(
            text=l(ctx, 'commons.createdBy') % 'Naegin#0049',
            icon_url='https://cdn.naeg.in/i/naegin-avatar.gif'
        )

        for name, cog in self.lite.cogs.items():
            cmds = [c for c in cog.get_commands() if not c.hidden]
            value = ', '.join([f'`{c}`' for c in cmds])

            if value:
                em.add_field(name=l(ctx, 'commands.help.categoryCommands') % (name, len(cmds)),
                    value=value)

        em.add_field(
            name='\u200b',
            value=l(ctx, 'commands.help.tip') % f'{ctx.prefix}{ctx.invoked_with}'
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='botinfo', aliases=['nodes', 'bi', 'statistics'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _bot_info(self, ctx):
        shard_ping = int(self.lite.shards[ctx.guild.shard_id].ws.latency * 1000)

        em = discord.Embed(
            colour=self.lite.color[0],
            title=l(ctx, 'commands.botinfo.statistics'),
            description=l(ctx, 'commands.botinfo.links') % ('https://discord.gg/qN5886E',
                                                            'https://lite.discobot.site',
                                                            'https://botsparadiscord.xyz/bots/discolite',
                                                            'https://github.com/Naegin/DiscoLite')
        ).set_author(
            name=ctx.me.name,
            icon_url=ctx.me.avatar_url
        ).set_footer(
            text=l(ctx, 'commons.createdBy') % 'Naegin#0049',
            icon_url='https://cdn.naeg.in/i/naegin-avatar.gif'
        ).set_thumbnail(
            url=ctx.me.avatar_url
        ).add_field(
            name=l(ctx, 'commands.botinfo.generalInfoTitle'),
            value=l(ctx, 'commands.botinfo.generalInfoDesc') % (ctx.guild.shard_id+1,
                                                                len(self.lite.shards),
                                                                shard_ping,
                                                                len(self.lite.guilds),
                                                                len(set(self.lite.get_all_members())),
                                                                len(self.lite.wavelink.players),
                                                                len(self.lite.wavelink.nodes),
                                                                self.lite.invoked_commands),
            inline=False
        )

        for identifier, node in self.lite.wavelink.nodes.items():
            stats = node.stats

            em.add_field(
                name=f'**LAVALINK NODE {identifier}**',
                value=l(ctx, 'commands.botinfo.nodeInfo') % (node.region.title().replace("_", " "),
                                                            get_length(stats.uptime, True),
                                                            stats.playing_players,
                                                            stats.players,
                                                            naturalsize(stats.memory_used))
            )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='invite', aliases=['add', 'adicionar', 'convite', 'convidar'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _invite(self, ctx):
        em = discord.Embed(
            colour=self.lite.color[1],
            description=l(ctx, 'commands.invite.text') % 'https://lite.discobot.site'
        ).set_author(
            name=ctx.me.name,
            icon_url=ctx.me.avatar_url
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='ping', aliases=['latency'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _ping(self, ctx):
        ping = int(self.lite.shards[ctx.guild.shard_id].ws.latency * 1000)
        await ctx.send(f'{self.lite.emoji["wireless"]} **Ping**: **`{ping}ms`**')

def setup(lite):
    lite.add_cog(Info(lite))