from discord.ext import commands
from discord.ext.commands.errors import *
from datetime import datetime
from utils import MusicError
from os import environ

import discord

class Events(commands.Cog):
    def __init__(self, lite):
        self.lite = lite

        self.lite.loop.create_task(self._fetch_logs_channels())

    async def _fetch_logs_channels(self):
        self.guild_logs = await self.lite.fetch_channel(int(environ['GUILDS_CHANNEL_ID']))
        self.error_logs = await self.lite.fetch_channel(int(environ['ERRORS_CHANNEL_ID']))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.lite._guilds.get(guild.id)

        humans = 0;bots = 0
        for member in guild.members:
            if member.bot: bots+=1
            else: humans+=1

        em = discord.Embed(
            colour=0x00ff00,
            timestamp=guild.me.joined_at,
            title='Mais um servidor!'
        ).set_author(
            name=guild.name,
            icon_url=guild.icon_url
        ).set_thumbnail(
            url=guild.icon_url
        ).set_footer(
            text=f'Servidores: {len(self.lite.guilds)}'
        ).add_field(
            name='Data de Criação',
            value=f'{guild.created_at.strftime("%d/%m/%y (%H:%M)")}'
        ).add_field(
            name='ID',
            value=str(guild.id)
        ).add_field(
            name='Dono',
            value=f'{guild.owner}\n`{guild.owner.id}`'
        ).add_field(
            name=f'Membros ({guild.member_count})',
            value=f'Humanos: {humans}\nBots: {bots}'
        )

        await self.guild_logs.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.lite._guilds.get(guild.id)

        humans = 0;bots = 0
        for member in guild.members:
            if member.bot: bots+=1
            else: humans+=1

        em = discord.Embed(
            colour=0xfc4b4b,
            timestamp=datetime.utcnow(),
            title='Menos um servidor...'
        ).set_author(
            name=guild.name,
            icon_url=guild.icon_url
        ).set_thumbnail(
            url=guild.icon_url
        ).set_footer(
            text=f'Servidores: {len(self.lite.guilds)}'
        ).add_field(
            name='Data de Criação',
            value=f'{guild.created_at.strftime("%d/%m/%y (%H:%M)")}'
        ).add_field(
            name='ID',
            value=str(guild.id)
        ).add_field(
            name='Dono',
            value=f'{guild.owner}\n`{guild.owner.id}`'
        ).add_field(
            name=f'Membros ({guild.member_count})',
            value=f'Humanos: {humans}\nBots: {bots}'
        )

        await self.guild_logs.send(embed=em)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        if isinstance(e, MusicError):
            await ctx.send(e)

        elif isinstance(e, CommandOnCooldown):
            _, s = divmod(e.retry_after, 60)
            await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, aguarde **`{int(s)}`**'
                ' segundo(s) para poder usar esse comando novamente.', delete_after=s+6)

        elif isinstance(e, MissingRole):
            await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você precisa do '
                f'cargo **`{e.missing_role[0] or "DJ"}`** para poder usar esse comando.')

        elif isinstance(e, (ConversionError, UserInputError)):
            if ctx.prefix == f'<@{ctx.me.id}> ':
                ctx.prefix = f'@{ctx.me.name} '

            await ctx.send(f'{self.lite.emoji["false"]} Parece que você usou o comando de forma '
                f'errada, **{ctx.author.name}**.\n**Uso correto: '
                f'`{ctx.prefix}{ctx.invoked_with} {ctx.command.usage}`**')

        elif isinstance(e, MissingPermissions):
            perms = '\n'.join([f'{self.lite.emoji["idle"]} **`{p.upper().replace("_", " ")}`**' for p in e.missing_perms])
            await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você precisa das seguintes'
                f' permissões para poder usar esse comando:\n\n{perms}')

        elif isinstance(e, BotMissingPermissions):
            perms = '\n'.join([f'{self.lite.emoji["idle"]} **`{p.upper().replace("_", " ")}`**' for p in e.missing_perms])
            await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, eu preciso das seguintes'
                f' permissões para poder rodar esse comando:\n\n{perms}')

        else:
            em = discord.Embed(
                colour=0xFF0000,
                timestamp=ctx.message.created_at,
                description=f'> {ctx.message.content}\n```py\n{e.__class__.__name__}: {e}```'
            ).set_author(
                name=f'{ctx.author} ({ctx.author.id})',
                icon_url=ctx.author.avatar_url
            ).set_footer(
                text=f'ID: {ctx.message.id}'
            )

            await self.error_logs.send(content=f'Comando executado no canal {ctx.channel} ({ctx.channel.id})'
                f' do servidor {ctx.guild} ({ctx.guild.id}).', embed=em)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.lite.invoked_commands += 1

        self.lite.log.info(f'Comando "{ctx.command}" usado por {ctx.author} {ctx.author.id} '
            f'em {ctx.guild} {ctx.guild.id}')

def setup(lite):
    lite.add_cog(Events(lite))