import traceback
from datetime import datetime
from os import environ
from random import randint

import discord
from discord.ext import commands
from discord.ext.commands.errors import *

from utils import SUPPORT_GUILD_INVITE_URL, PATREON_DONATE_URL
from utils.errors import DiscoError, WaitingForPreviousChoice


class Events(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

        self.disco.loop.create_task(self._fetch_logs_channels())

    async def _fetch_logs_channels(self):
        self.guild_logs = await self.disco.fetch_channel(int(environ['GUILDS_CHANNEL_ID']))
        self.error_logs = await self.disco.fetch_channel(int(environ['ERRORS_CHANNEL_ID']))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        g = self.disco._guilds.get(guild.id)
        if str(guild.region) == 'brazil':
            g.update({"options.locale": "pt_BR"})

        humans = 0
        bots = 0
        for member in guild.members:
            if member.bot:
                bots += 1
            else:
                humans += 1

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
            text=f'Servidores: {len(self.disco.guilds)}'
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
        ).add_field(
            name='Região',
            value=f'`{guild.region}`'
        )

        await self.guild_logs.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.disco._guilds.get(guild.id).delete()

        humans = 0
        bots = 0
        for member in guild.members:
            if member.bot:
                bots += 1
            else:
                humans += 1

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
            text=f'Servidores: {len(self.disco.guilds)}'
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
        ).add_field(
            name='Região',
            value=f'`{guild.region}`'
        )

        await self.guild_logs.send(embed=em)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        if not isinstance(e, WaitingForPreviousChoice) and hasattr(ctx, '_remove_from_waiting'):
            if ctx.author.id in self.disco._waiting_for_choice:
                self.disco._waiting_for_choice.remove(ctx.author.id)

        original = e.__cause__
        if isinstance(original, (discord.NotFound, discord.Forbidden)):
            return

        if isinstance(e, DiscoError):
            await ctx.send(e)

        elif isinstance(e, CommandOnCooldown):
            if ctx.command.name == 'whatsmyprefix' and ctx.prefix == f'@{ctx.me.name} ':
                return

            _, s = divmod(e.retry_after, 60)
            await ctx.send(ctx.t('errors.onCooldown', {"emoji": self.disco.emoji["false"],
                                                       "author": ctx.author.name,
                                                       "cooldown": int(s)}),
                           delete_after=s + 6)

        elif isinstance(e, MissingRole):
            await ctx.send(ctx.t('errors.missingRole', {"emoji": self.disco.emoji["false"],
                                                        "role": e.missing_role[0] or "DJ",
                                                        "author": ctx.author.name}))

        elif isinstance(e, (ConversionError, UserInputError)):
            usage = (ctx.t(f'commands.{ctx.command.qualified_name}.meta') or {}).get('usage')
            await ctx.send(ctx.t('errors.inputError', {"emoji": self.disco.emoji["false"],
                                                       "usage": f'{ctx.prefix}{ctx.invoked_with}'
                                                                + (' ' + usage if usage else ''),
                                                       "author": ctx.author.name}))

        elif isinstance(e, MissingPermissions):
            perms = '\n'.join(
                [f'{self.disco.emoji["idle"]} **`{ctx.t("permissions." + p).upper()}`**' for p in e.missing_perms])
            await ctx.send(ctx.t('errors.missingPermissions', {"emoji": self.disco.emoji["false"],
                                                               "permissions": perms,
                                                               "author": ctx.author.name}))

        elif isinstance(e, BotMissingPermissions):
            perms = '\n'.join(
                [f'{self.disco.emoji["idle"]} **`{ctx.t("permissions." + p).upper()}`**' for p in e.missing_perms])
            await ctx.send(ctx.t('errors.botMissingPermissions', {"emoji": self.disco.emoji["false"],
                                                                  "permissions": perms,
                                                                  "author": ctx.author.name}))

        elif isinstance(e, DisabledCommand):
            await ctx.send(ctx.t('errors.disabledCommand', {"emoji": self.disco.emoji["false"],
                                                            "author": ctx.author.name,
                                                            "command": ctx.command.qualified_name,
                                                            "reason": ctx.command.disabled_reason
                                                                      or ctx.t('commons.unknown')}))

        else:
            traceback_ = ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))

            em = discord.Embed(
                colour=0xFF0000,
                timestamp=ctx.message.created_at,
                description=f'```py\n{traceback_[:2038]}```'
            ).set_author(
                name=f'{ctx.author} ({ctx.author.id})',
                icon_url=ctx.author.avatar_url
            ).set_footer(
                text=f'ID: {ctx.message.id}'
            )

            await self.error_logs.send(content=f'Comando executado no canal {ctx.channel} ({ctx.channel.id})'
                                               f' do servidor {ctx.guild} ({ctx.guild.id}).'
                                               f'\n> {ctx.message.content[:1500]}', embed=em)

            await ctx.send(ctx.t('errors.unexpectedError', {"emoji": self.disco.emoji["false"],
                                                            "author": ctx.author.name,
                                                            "command": ctx.command.qualified_name,
                                                            "support": SUPPORT_GUILD_INVITE_URL}))

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.disco.invoked_commands += 1

        self.disco.log.info(f'Comando "{ctx.command}" usado por {ctx.author} {ctx.author.id} '
                            f'em {ctx.guild} {ctx.guild.id}')

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if hasattr(ctx, '_remove_from_waiting'):
            if ctx.author.id in self.disco._waiting_for_choice:
                self.disco._waiting_for_choice.remove(ctx.author.id)

        if ctx.command.name not in ['donate', 'whatsmyprefix'] and randint(1, 7) == 1:
            await ctx.send(ctx.t('commands.donate.text', {"emoji": self.disco.emoji["featured"],
                                                          "link": PATREON_DONATE_URL}))


def setup(disco):
    disco.add_cog(Events(disco))
