from discord.ext import commands
from discord.ext.commands.errors import *
from datetime import datetime
from utils import MusicError
from os import environ

import discord

class Events(commands.Cog):
    def __init__(self, lite):
        self.lite = lite

        lite.loop.create_task(self._get_webhook())
    
    async def _get_webhook(self):
        self.webhook = await self.lite.fetch_webhook(int(environ['GUILDS_WEBHOOK_ID']))
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
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

        await self.webhook.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
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

        await self.webhook.send(embed=em)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        if isinstance(e, MusicError):
            await ctx.send(e)

        if isinstance(e, CommandOnCooldown):
            _, s = divmod(e.retry_after, 60)
            await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, aguarde **`{int(s)}`**'
                ' segundo(s) para poder usar esse comando novamente.', delete_after=s+6)
        
        elif isinstance(e, MissingRole):
            await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author.name}**, você precisa do '
                'cargo **`DJ`** para poder usar esse comando.')
        
        elif isinstance(e, (ConversionError, UserInputError)):
            await ctx.send(f'{self.lite.emoji["false"]} Parece que você usou o comando de forma '
                f'errada, **{ctx.author.name}**.\n**Uso correto: '
                f'`{ctx.prefix}{ctx.invoked_with} {ctx.command.usage}`**')

        elif isinstance(e, BotMissingPermissions):
            perms = '\n'.join([f'{self.lite.emoji["idle"]} **`{p.upper().replace("_", " ")}`**' for p in e.missing_perms])
            await ctx.send(f'{self.lite.emoji["false"]} **{ctx.author}**, eu preciso das seguintes'
                f' permissões para poder rodar esse comando.\n\n{perms}')

def setup(lite):
    lite.add_cog(Events(lite))