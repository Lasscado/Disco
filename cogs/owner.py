import math
import os
import typing

import discord
from discord.ext import commands

from utils import get_length, TRANSPARENT_IMAGE_URL


class Owner(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, disco):
        self.disco = disco

        self.disco.loop.create_task(self._fetch_logs_channels())

    async def _fetch_logs_channels(self):
        self.ban_logs = await self.disco.fetch_channel(int(os.environ['GLOBAL_BANS_CHANNEL_ID']))

    @commands.command(name='eval')
    @commands.is_owner()
    async def _eval(self, ctx, *, code):
        try:
            if code.startswith('await '):
                code = await eval(code[6:])
            else:
                code = eval(code)

            await ctx.send(f'```py\n{code}```')
        except Exception as e:
            await ctx.send(f'```py\n{e.__class__.__name__}: {e}```')

    @commands.command(name='reload', aliases=['rl'])
    @commands.is_owner()
    async def _reload(self, ctx, plugin):
        self.disco.reload_extension('cogs.' + plugin)
        await ctx.message.add_reaction(self.disco.emoji["true"])

    @commands.command(name='load', aliases=['ld'])
    @commands.is_owner()
    async def _load(self, ctx, plugin):
        self.disco.load_extension('cogs.' + plugin)
        await ctx.message.add_reaction(self.disco.emoji["true"])

    @commands.command(name='unload', aliases=['ul'])
    @commands.is_owner()
    async def _unload(self, ctx, plugin):
        self.disco.unload_extension('cogs.' + plugin)
        await ctx.message.add_reaction(self.disco.emoji["true"])

    @commands.command(name='disablecommandglobal', aliases=['dcmdg'])
    @commands.is_owner()
    async def _disable_command_global(self, ctx, command, *, reason=None):
        command = self.disco.get_command(command)
        if command is None:
            return await ctx.send(self.disco.emoji["false"])

        if command.enabled:
            command.enabled = False
            command.disabled_reason = reason
            await ctx.send('Desativado.')
        else:
            command.enabled = True
            await ctx.send('Ativado.')

    @commands.command(name='globalban', aliases=['gban'], usage='<Guild/User> <ID> <Motivo>')
    @commands.is_owner()
    async def _global_ban(self, ctx, target_type, target_id: int, *, reason):
        target_type = target_type.lower()

        if ban := await self.disco.db.get_last_ban(target_id=target_id):
            return await ctx.send(f'{self.disco.emoji["false"]} **{ctx.author.name}**, esse alvo '
                                  f'já está banido do meu sistema por `{ban}`.')

        if target_type in ['user', 'u']:
            try:
                target = await self.disco.fetch_user(target_id)
            except discord.NotFound:
                return await ctx.message.add_reaction(self.disco.emoji["false"])

            self.disco.user_blacklist.add(target.id)

            icon = target.avatar_url
            target_type = 'Usuário'
        elif target_type in ['server', 'guild', 'g']:
            try:
                target = await self.disco.fetch_guild(target_id)
            except discord.NotFound:
                return await ctx.message.add_reaction(self.disco.emoji["false"])

            self.disco.guild_blacklist.add(target.id)
            await target.leave()

            icon = target.icon_url
            target_type = 'Servidor'
        else:
            raise commands.UserInputError()

        await self.disco.db.register_ban(target_id=target.id,
                                         author_id=ctx.author.id,
                                         is_guild=isinstance(target, discord.Guild),
                                         reason=reason)

        await ctx.message.add_reaction(self.disco.emoji["true"])

        em = discord.Embed(
            colour=0xb10448,
            title=f'Banimento Global #{await self.disco.db.total_bans} | {target_type}',
            timestamp=ctx.message.created_at
        ).set_author(
            name=str(target),
            icon_url=icon
        ).set_footer(
            text=f'ID: {target.id}'
        ).set_thumbnail(
            url=icon
        ).add_field(
            name='**Data de Criação** ::',
            value=target.created_at.strftime('%d/%m/%y (%H:%M)')
        ).add_field(
            name='**Moderador** ::',
            value=f'{ctx.author}\n`{ctx.author.id}`'
        ).add_field(
            name='**Motivo** ::',
            value=reason
        )

        await self.ban_logs.send(embed=em)

    @commands.command(name='commandhistory', aliases=['cmdhistory'])
    @commands.bot_has_permissions(embed_links=True)
    @commands.is_owner()
    async def _command_history(self, ctx, user: typing.Union[discord.User, int], page: int = 1):
        if type(user) is int:
            try:
                user = await self.disco.fetch_user(user)
            except discord.NotFound:
                await ctx.send(self.disco.emoji["false"] + ' Não foi possível encontrar um usuário com o ID fornecido.')
                return

        if user.bot:
            await ctx.send('%s **`%s`** é um bot!' % (self.disco.emoji["false"], user))
            return

        if not (total_entries := await self.disco.db.total_command_history_entries_for(user.id)):
            await ctx.send('%s Nenhum registro de comando encontrado para **`%s`**.' % (self.disco.emoji["false"],
                                                                                        user))
            return

        total_pages = math.ceil(total_entries / (per_page := 20))
        current_page = page if 0 < page <= total_pages else 1
        entries = await self.disco.db.get_command_history_from(user.id, limit=per_page,
                                                               skip=(current_page - 1) * per_page)

        em = discord.Embed(
            colour=self.disco.color[0],
            title='Histórico de Comandos',
            description='\n'.join('`[%s]`: __**%s**__ (%ss)' % (e.invoked_at.strftime('%d/%m/%y %H:%M'),
                                                                e.command, e.duration) for e in entries)
        ).set_author(
            name=str(user),
            icon_url=user.avatar_url
        ).set_thumbnail(
            url=TRANSPARENT_IMAGE_URL
        ).set_footer(
            text='Página %s/%s' % (current_page, total_pages)
        )

        await ctx.send(ctx.author.mention, embed=em)


def setup(disco):
    disco.add_cog(Owner(disco))
