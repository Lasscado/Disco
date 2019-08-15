from discord.ext import commands
from discord.ext.commands.errors import *
from datetime import datetime
from random import randint
from utils import MusicError, PremiumFeature, PremiumLowLevel, l
from os import environ

import discord
import re

PREMIUM_LVL_ROLE = re.compile('^Level [1-9]{1,2}$')

class Events(commands.Cog):
    def __init__(self, disco):
        self.disco = disco
        self.support_guild = environ['SUPPORT_GUILD_ID']

        self.disco.loop.create_task(self._fetch_logs_channels())

    async def _fetch_logs_channels(self):
        self.guild_logs = await self.disco.fetch_channel(int(environ['GUILDS_CHANNEL_ID']))
        self.error_logs = await self.disco.fetch_channel(int(environ['ERRORS_CHANNEL_ID']))

    @commands.Cog.listener()
    async def on_member_leave(self, member):
        if member.bot or member.guild.id != self.support_guild:
            return

        premium = member.guild.get_role(int(environ['PREMIUM_ROLE_ID']))
        if premium in member.roles:
            self.disco._users.get(member.id).update({
                "premium.level": 0,
                "premium.enabledAt": None,
                "premium.expiresAt": None
            })

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if after.bot or after.guild.id != self.support_guild:
            return

        premium = after.guild.get_role(int(environ['PREMIUM_ROLE_ID']))
        if premium not in after.roles and premium in before.roles:
            self.disco._users.get(after.id).update({
                "premium.level": 0,
                "premium.enabledAt": None,
                "premium.expiresAt": None
            })

            level = discord.utils.find(lambda r: PREMIUM_LVL_ROLE.match(r.name), after.roles)
            if level:
                await after.remove_roles(level)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        g = self.disco._guilds.get(guild.id)
        if guild.region.name == 'brazil':
            g.update({"options.locale": "pt-BR"})

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
        )

        await self.guild_logs.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        self.disco._guilds.get(guild.id).delete()

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
        )

        await self.guild_logs.send(embed=em)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, e):
        if isinstance(e, MusicError):
            await ctx.send(e)

        elif isinstance(e, PremiumFeature):
            await ctx.send(l(ctx, 'errors.premiumFeature', {"author": ctx.author.name,
                "emoji": self.disco.emoji["featured"], "link": "https://patreon.com/discobot"}))

        elif isinstance(e, PremiumLowLevel):
            await ctx.send(l(ctx, 'errors.premiumLowLevel', {"author": ctx.author.name,
                "level": ctx._author.data['premium']['level'], "required": e.required_level,
                "emoji": self.disco.emoji["featured"], "link": "https://patreon.com/discobot"}))

        elif isinstance(e, CommandOnCooldown):
            _, s = divmod(e.retry_after, 60)
            await ctx.send(l(ctx, 'errors.onCooldown', {"emoji": self.disco.emoji["false"],
                "author": ctx.author.name, "cooldown": int(s)}), delete_after=s+6)

        elif isinstance(e, MissingRole):
            await ctx.send(l(ctx, 'errors.missingRole', {"emoji": self.disco.emoji["false"],
                "role": e.missing_role[0] or "DJ", "author": ctx.author.name}))

        elif isinstance(e, (ConversionError, UserInputError)):
            if ctx.prefix == f'<@{ctx.me.id}> ':
                ctx.prefix = f'@{ctx.me.name} '

            usage = l(ctx, f'commands.{ctx.command.name}.cmdUsage')
            await ctx.send(l(ctx, 'errors.inputError', {"emoji": self.disco.emoji["false"],
                "usage": f'{ctx.prefix}{ctx.invoked_with} {usage if usage else ""}',
                "author": ctx.author.name}))

        elif isinstance(e, MissingPermissions):
            perms = '\n'.join([f'{self.disco.emoji["idle"]} **`{l(ctx, "permissions." + p).upper()}`**' for p in e.missing_perms])
            await ctx.send(l(ctx, 'errors.missingPermissions', {"emoji": self.disco.emoji["false"],
                "permissions": perms, "author": ctx.author.name}))

        elif isinstance(e, BotMissingPermissions):
            perms = '\n'.join([f'{self.disco.emoji["idle"]} **`{l(ctx, "permissions." + p).upper()}`**' for p in e.missing_perms])
            await ctx.send(l(ctx, 'errors.botMissingPermissions', {"emoji": self.disco.emoji["false"],
                "permissions": perms, "author": ctx.author.name}))

        elif ctx.command.name == 'play' and ctx.author.id in ctx.cog.waiting:
            ctx.cog.waiting.remove(ctx.author.id)

        elif not isinstance(e, (discord.NotFound, discord.Forbidden)):
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
        self.disco.invoked_commands += 1

        self.disco.log.info(f'Comando "{ctx.command}" usado por {ctx.author} {ctx.author.id} '
            f'em {ctx.guild} {ctx.guild.id}')

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.command.name != 'donate' and not ctx._author.data['premium']['level'] \
            and randint(1, 5) == 1:
            await ctx.send(l(ctx.locale, 'commands.donate.text', {
                "emoji": self.disco.emoji["featured"], "link": "https://patreon.com/discobot"}))

def setup(disco):
    disco.add_cog(Events(disco))