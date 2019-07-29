from discord.ext import commands
from discord.ext.commands.errors import *
from datetime import datetime
from utils import MusicError, l
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
        g = self.lite._guilds.get(guild.id)
        if not guild.region.name == 'brazil':
            g.update({"options.locale": "en-US"})

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
        self.lite._guilds.get(guild.id).delete()

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
            await ctx.send(l(ctx, 'errors.onCooldown') % (self.lite.emoji["false"],
                ctx.author.name, int(s)), delete_after=s+6)

        elif isinstance(e, MissingRole):
            await ctx.send(l(ctx, 'errors.missingRole') % (self.lite.emoji["false"],
                ctx.author.name, e.missing_role[0] or "DJ"))

        elif isinstance(e, (ConversionError, UserInputError)):
            if ctx.prefix == f'<@{ctx.me.id}> ':
                ctx.prefix = f'@{ctx.me.name} '

            usage = l(ctx, f'commands.{ctx.command.name}.cmdUsage')
            await ctx.send(l(ctx, 'errors.inputError') % (self.lite.emoji["false"],
                ctx.author.name, f'{ctx.prefix}{ctx.invoked_with} {usage if usage else ""}'))

        elif isinstance(e, MissingPermissions):
            perms = '\n'.join([f'{self.lite.emoji["idle"]} **`{l(ctx, "permissions." + p).upper()}`**' for p in e.missing_perms])
            await ctx.send(l(ctx, 'errors.missingPermissions') % (self.lite.emoji["false"],
                ctx.author.name, perms))

        elif isinstance(e, BotMissingPermissions):
            perms = '\n'.join([f'{self.lite.emoji["idle"]} **`{l(ctx, "permissions." + p).upper()}`**' for p in e.missing_perms])
            await ctx.send(l(ctx, 'errors.botMissingPermissions') % (self.lite.emoji["false"],
                ctx.author.name, perms))

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