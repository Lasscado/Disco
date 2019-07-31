from discord.ext import commands

import os
import sys
import discord

class Owner(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

        self.disco.loop.create_task(self._fetch_logs_channels())

    async def _fetch_logs_channels(self):
       self.ban_logs = await self.disco.fetch_channel(int(os.environ['GLOBAL_BANS_CHANNEL_ID']))

    @commands.command(name='eval', hidden=True)
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

    @commands.command(name='reload', aliases=['rl'], hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx, plugin):
        try:
            self.disco.reload_extension('plugins.' + plugin)
            await ctx.message.add_reaction('<:discoTrue:512912547108749312>')
        except Exception as e:
            await ctx.send(f'```py\n{e.__class__.__name__}: {e}```')
            await ctx.message.add_reaction('<:discoFalse:512912546869673999>')

    @commands.command(name='load', aliases=['ld'], hidden=True)
    @commands.is_owner()
    async def _load(self, ctx, plugin):
        try:
            self.disco.load_extension('plugins.' + plugin)
            await ctx.message.add_reaction('<:discoTrue:512912547108749312>')
        except Exception as e:
            await ctx.send(f'```py\n{e.__class__.__name__}: {e}```')
            await ctx.message.add_reaction('<:discoFalse:512912546869673999>')

    @commands.command(name='unload', aliases=['ul'], hidden=True)
    @commands.is_owner()
    async def _unload(self, ctx, plugin):
        try:
            self.disco.unload_extension('plugins.' + plugin)
            await ctx.message.add_reaction('<:discoTrue:512912547108749312>')
        except Exception as e:
            await ctx.send(f'```py\n{e.__class__.__name__}: {e}```')
            await ctx.message.add_reaction('<:discoFalse:512912546869673999>')

    @commands.command(name='globalban', aliases=['gban'], hidden=True,
        usage='<Guild/User> <ID> <Motivo>')
    @commands.is_owner()
    async def _global_ban(self, ctx, target_type, target_id: int, *, reason):
        target_type = target_type.lower()

        if self.disco._bans.find(targetID=target_id, ignore=False):
            return await ctx.send(f'{self.disco.emoji["false"]} **{ctx.author.name}**, esse alvo '
                'já está banido do meu sistema.')

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

        self.disco._bans.new(
            target_id=target.id,
            author_id=ctx.author.id,
            is_guild=isinstance(target, discord.Guild),
            reason=reason
        )

        await ctx.message.add_reaction(self.disco.emoji["true"])

        em = discord.Embed(
            colour=0xb10448,
            title=f'Banimento Global #{self.disco._bans.total} | {target_type}',
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

def setup(disco):
    disco.add_cog(Owner(disco))