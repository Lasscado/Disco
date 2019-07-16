from discord.ext import commands
from humanize import naturalsize
from datetime import datetime
from utils import get_length

import discord

TRANSPARENT = 'https://cdn.discordapp.com/attachments/359388328233140239/471181808612933634/invisible.png'

class Info(commands.Cog, name='Informações'):
    def __init__(self, lite):
        self.lite = lite

    @commands.command(name='help', aliases=['ajuda', 'commands', 'cmds'], usage='[Comando]',
        description='Lista detalhadamente todos os comandos do Bot.')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def _help(self, ctx, command=None):
        if command:
            cmd = self.lite.get_command(command)
            if not cmd:
                return await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, eu não'
                    ' encontrei nenhum comando com o nome fornecido.')

            em = discord.Embed(
                colour=self.lite.color[0],
                title=f'Comando {cmd.name.title()}'
            ).set_author(
                name=ctx.me.name,
                icon_url=ctx.me.avatar_url
            ).set_thumbnail(
                url=TRANSPARENT
            ).add_field(
                name='Descrição',
                value=cmd.description or 'Não fornecida.'
            ).add_field(
                name='Uso',
                value=f'{ctx.prefix}{cmd.name} {cmd.usage}' if cmd.usage else 'Não especificado.'
            ).add_field(
                name='Outros Nomes',
                value=', '.join([f'`{a}`' for a in cmd.aliases]) or 'Não definidos.'
            )

            return await ctx.send(content=ctx.author.mention, embed=em)

        em = discord.Embed(
            colour=self.lite.color[0],
            description='[**Servidor de Suporte**](https://discord.gg/qN5886E) | ' \
                '[**Adicionar**](https://lite.discobot.site) | ' \
                '[**Votar**](https://botsparadiscord.xyz/bots/discolite)\n\n' \
                '**[Prefixos]:** `d!comando`, `li comando`\n\u200b'
        ).set_author(
            name=ctx.me.name,
            icon_url=ctx.me.avatar_url
        ).set_thumbnail(
            url=ctx.me.avatar_url
        ).set_footer(
            text=f'Hospedado em 1 x Raspberry Pi 3B+',
            icon_url='https://cdn.discordapp.com/emojis/599610426581450788.png'
        )

        for name, cog in self.lite.cogs.items():
            cmds = [c for c in cog.get_commands() if not c.hidden]
            value = ', '.join([f'`{c}`' for c in cmds])

            if value:
                em.add_field(name=f'**Comandos de {name}**: ({len(cmds)})', value=value)

        em.add_field(
            name='\u200b',
            value=f'Digite **{ctx.prefix}{ctx.invoked_with} <Comando>** para ver mais ' \
                'informações sobre um comando.'
        )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='botinfo', aliases=['ping', 'latency', 'nodes', 'bi', 'statistics'],
        description='Mostra informações sobre o Bot.')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def _bot_info(self, ctx):
        shard_ping = int(self.lite.shards[ctx.guild.shard_id].ws.latency * 1000)

        em = discord.Embed(
            colour=self.lite.color[0],
            timestamp=ctx.message.created_at,
            title='Estatísticas',
            description='[**Servidor de Suporte**](https://discord.gg/qN5886E) | ' \
                '[**Adicionar**](https://lite.discobot.site) | ' \
                '[**Votar**](https://botsparadiscord.xyz/bots/discolite)\n\u200b'
        ).set_author(
            name=ctx.me.name,
            icon_url=ctx.me.avatar_url
        ).set_footer(
            text=f'Hospedado em 1 x Raspberry Pi 3B+',
            icon_url='https://cdn.discordapp.com/emojis/599610426581450788.png'
        ).set_thumbnail(
            url=ctx.me.avatar_url
        ).add_field(
            name='**INFORMAÇÕES BÁSICAS**',
            value=f'**Ping** `[Shard {ctx.guild.shard_id+1}/{len(self.lite.shards)}]`: {shard_ping}ms\n' \
                f'**Servidores**: {len(self.lite.guilds)}\n' \
                f'**Membros**: {len(set(self.lite.get_all_members()))}\n' \
                f'**Players**: {len(self.lite.wavelink.players)}\n' \
                f'**Lavalink Nodes**: {len(self.lite.wavelink.nodes)}\n\u200b',
            inline=False
        )

        for identifier, node in self.lite.wavelink.nodes.items():
            stats = node.stats

            em.add_field(
                name=f'**LAVALINK NODE {identifier}**',
                value=f'**Região**: {node.region.title().replace("_", " ")}\n' \
                    f'**Uptime**: {get_length(stats.uptime, True)}\n' \
                    f'**Players Ativos**: {stats.playing_players}/{stats.players}\n' \
                    f'**Memória Usada**: {naturalsize(stats.memory_used)}\n' \
                    f'**Uso de CPU**: {int(stats.lavalink_load*1000)}%'
            )

        await ctx.send(content=ctx.author.mention, embed=em)

    @commands.command(name='invite', aliases=['add', 'adicionar', 'convite', 'convidar'],
        description='Envia o link de convite para adicionar o Bot.')
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def _invite(self, ctx):
        em = discord.Embed(
            colour=self.lite.color[1],
            description=f'[Clique aqui para adicionar o **Disco Lite** em seu servidor]' \
                '(https://lite.discobot.site)'
        ).set_author(
            name=ctx.me.name,
            icon_url=ctx.me.avatar_url
        )

        await ctx.send(content=ctx.author.mention, embed=em)

def setup(lite):
    lite.add_cog(Info(lite))