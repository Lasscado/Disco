import traceback
from datetime import datetime
from os import environ
from random import randint

import discord
from babel.dates import format_datetime
from discord.ext import commands
from discord.ext.commands.errors import *

from utils import TextUploader, SUPPORT_GUILD_INVITE_URL, PATREON_DONATE_URL, BANNER_URL, DBOTS_PAGE_URL
from utils.errors import DiscoError, WaitingForPreviousChoice


class Events(commands.Cog):
    def __init__(self, disco):
        self.disco = disco
        self.text_uploader = TextUploader(disco, int(environ['TEXT_UPLOADER_CATEGORY_ID']))

        self.disco.loop.create_task(self._fetch_logs_channels())

    def can_send(self, channel):
        perms = channel.permissions_for(channel.guild.me)
        return perms.send_messages and perms.embed_links

    async def _fetch_logs_channels(self):
        self.guild_logs = await self.disco.fetch_channel(int(environ['GUILDS_CHANNEL_ID']))
        self.error_logs = await self.disco.fetch_channel(int(environ['ERRORS_CHANNEL_ID']))

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        gdb = await self.disco.db.get_guild(guild.id)
        if str(guild.region) == 'brazil':
            await gdb.set({"options.locale": "pt_BR"})

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
        if gdb := await self.disco.db.get_guild(guild.id):
            await gdb.delete()

        try:
            del self.disco._prefixes[guild.id]
        except KeyError:
            pass

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
            traceback_ = ''.join(traceback.format_exception(type(e), e, e.__traceback__))

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

        if ctx.command.name not in ['donate', 'whatsmyprefix'] and randint(1, 9) == 1:
            await ctx.send(ctx.t('commands.donate.text', {"emoji": self.disco.emoji["featured"],
                                                          "link": PATREON_DONATE_URL}))

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        if payload.guild_id is None:
            return

        options = (await self.disco.db.get_guild(payload.guild_id)).options
        logs = (guild := self.disco.get_guild(payload.guild_id)).get_channel(options['message_logs_channel'])
        if logs is None or not self.can_send(logs):
            return

        t = self.disco.i18n.get_t(locale := options['locale'])
        if messages := await self.disco.db.get_messages(list(payload.message_ids)):
            unknown = t('commons.unknownUser')
            content = t('events.bulkMessageDeleteLog', {"banner": BANNER_URL,
                                                        "url": DBOTS_PAGE_URL,
                                                        "guild": guild,
                                                        "channel": guild.get_channel(payload.channel_id),
                                                        "date": format_datetime(datetime.utcnow(), locale=locale)}) \
                      + ''.join(f'\r\n\r\n[{format_datetime(message.created_at, locale=locale)} GMT] '
                                f'{guild.get_member(message.author_id) or unknown} ({message.author_id}) : '
                                + message.content for message in messages)

            view, download = await self.text_uploader.upload(t('commons.deletedMessages'), content)
            msg = t('events.bulkMessageDelete', {"amount": len(payload.message_ids),
                                                 "channel": f'<#{payload.channel_id}>',
                                                 "view": view,
                                                 "download": download,
                                                 "saved": len(messages)})
        else:
            msg = t('events.bulkMessageDeleteUnknown', {"amount": len(payload.message_ids),
                                                        "channel": f'<#{payload.channel_id}>'})

        em = discord.Embed(description=msg,
                           colour=0xdb0f0f,
                           timestamp=datetime.utcnow())

        await logs.send(embed=em)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if payload.guild_id is None:
            return

        options = (await self.disco.db.get_guild(payload.guild_id)).options
        logs = self.disco.get_guild(payload.guild_id).get_channel(options['message_logs_channel'])
        if logs is None or not self.can_send(logs):
            return

        t = self.disco.i18n.get_t(options['locale'])
        if cached := await self.disco.db.get_message(payload.message_id):
            self.disco.loop.create_task(cached.delete())
            if (author := self.disco.get_user(cached.author_id)) and author.bot:
                return

            msg = t('events.messageDelete', {"author": f"<@{cached.author_id}>",
                                             "channel": f"<#{cached.channel_id}>"})
        else:
            author = None
            msg = t('events.messageDelete', {"author": t('commons.unknown'),
                                             "channel": f"<#{payload.channel_id}>"})

        em = discord.Embed(
            description=f'{msg}\n{cached.content[:2047 - len(msg)] if cached else ""}',
            colour=0xdb0f0f,
            timestamp=datetime.utcnow()
        ).set_footer(
            text=f'ID: {payload.message_id}'
        )

        if author:
            em.set_author(name=str(author), icon_url=author.avatar_url)

        await logs.send(embed=em)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if not (guild_id := int(payload.data.get('guild_id', 0))) or \
                not (author_id := int(payload.data.get('author', {}).get('id', 0))):
            return

        guild = self.disco.get_guild(guild_id)
        if (author := guild.get_member(author_id)) and author.bot:
            return

        options = (await self.disco.db.get_guild(guild_id)).options
        logs = self.disco.get_guild(guild_id).get_channel(options['message_logs_channel'])
        if logs is None or not self.can_send(logs):
            return

        t = self.disco.i18n.get_t(options['locale'])
        channel_id = payload.data['channel_id']
        msg = t('events.messageEdit', {"author": author.mention,
                                       "channel": f'<#{channel_id}>',
                                       "url": "https://discordapp.com/channels/%s/%s/%s" % (guild_id,
                                                                                            channel_id,
                                                                                            payload.message_id)})

        em = discord.Embed(
            description=msg,
            colour=0xfff705,
            timestamp=datetime.utcnow()
        ).set_author(
            name=str(author),
            icon_url=author.avatar_url
        ).set_footer(
            text=f'ID: {payload.message_id}'
        )

        new_content = payload.data['content']
        if cached := await self.disco.db.get_message(payload.message_id):
            em.add_field(name=t('commons.before'), value=cached.content[:1024] or '\u200b', inline=False)
            self.disco.loop.create_task(cached.edit(new_content))

        em.add_field(name=t('commons.after'), value=new_content[:1024], inline=False)

        await logs.send(embed=em)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        options = (await self.disco.db.get_guild(member.guild.id)).options
        if not member.bot \
                and member.guild.me.guild_permissions.manage_roles \
                and (auto_role := member.guild.get_role(options['auto_role'])) \
                and member.guild.me.top_role > auto_role:
            self.disco.loop.create_task(member.add_roles(auto_role, reason='Disco Auto Role'))

        logs = member.guild.get_channel(options['member_logs_channel'])
        if logs is None or not self.can_send(logs):
            return

        t = self.disco.i18n.get_t(options['locale'])

        em = discord.Embed(
            title=(self.disco.emoji['bot'] + ' ' if member.bot else '') + t('events.memberJoin'),
            description=member.mention,
            colour=0x414FCB,
            timestamp=member.joined_at
        ).set_author(
            name=str(member),
            icon_url=member.avatar_url
        ).set_thumbnail(
            url=member.avatar_url
        ).set_footer(
            text=f'ID: {member.id}'
        ).add_field(
            name=f'**{t("commons.accountCreation")}** ::',
            value='%s\n%s' % (format_datetime(member.created_at, format='short', locale=options["locale"]),
                              t('commons.daysAgo', {"days": (datetime.utcnow() - member.created_at).days}))
        ).add_field(
            name=f'**{t("commons.position")}** ::',
            value=f'#{member.guild.member_count}'
        )

        await logs.send(embed=em)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        options = (await self.disco.db.get_guild(member.guild.id)).options
        logs = member.guild.get_channel(options['member_logs_channel'])
        if logs is None or not self.can_send(logs):
            return

        t = self.disco.i18n.get_t(options['locale'])

        em = discord.Embed(
            title=(self.disco.emoji['bot'] + ' ' if member.bot else '') + t('events.memberLeave'),
            description=member.mention,
            colour=0xFF4A50,
            timestamp=datetime.utcnow()
        ).set_author(
            name=str(member),
            icon_url=member.avatar_url
        ).set_thumbnail(
            url=member.avatar_url
        ).set_footer(
            text=f'ID: {member.id}'
        ).add_field(
            name=f'**{t("commons.accountCreation")}** ::',
            value='%s\n%s' % (format_datetime(member.created_at, format='short', locale=options["locale"]),
                              t('commons.daysAgo', {"days": (datetime.utcnow() - member.created_at).days}))
        ).add_field(
            name=f'**{t("commons.joinedAt")}** ::',
            value='%s\n%s' % (format_datetime(member.joined_at, format='short', locale=options["locale"]),
                              t('commons.daysAgo', {"days": (datetime.utcnow() - member.joined_at).days}))
        )

        await logs.send(embed=em)


def setup(disco):
    disco.add_cog(Events(disco))
