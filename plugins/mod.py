import typing
from datetime import datetime
from random import randint

import discord
from discord.ext import commands

from utils import checks, TRANSPARENT_IMAGE_URL


class Moderation(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

    async def _mod_log(self, ctx, **kwargs):
        logs = ctx.guild.get_channel(ctx.gdb.options['mod_logs_channel'])
        if logs is None or (perms := ctx.me.permissions_in(logs)) and not (perms.send_messages and perms.embed_links):
            return

        case_id = int(str(await self.disco.db.total_mod_logs(ctx.guild.id)) + str(randint(100, 999)))
        reason = kwargs.get('reason')
        em = discord.Embed(
            title=ctx.t('commons.modAction', {"name": ctx.command.name.title()}),
            description=ctx.t(f'commands.{ctx.command.qualified_name}.logMessage', kwargs),
            colour=kwargs.get('colour'),
            timestamp=datetime.utcnow()
        ).set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url
        ).set_thumbnail(
            url=TRANSPARENT_IMAGE_URL
        ).set_footer(
            text=ctx.t('commons.caseId', {"id": case_id})
        )

        targets = kwargs.get('targets', [kwargs.get('user'), kwargs.get('channel')])
        for target in targets:
            if isinstance(target, (discord.User, discord.Member)):
                em.add_field(name=ctx.t('commons.user'), value='{0} ({0.mention})\n`{0.id}`'.format(target))
            elif isinstance(target, (discord.TextChannel, discord.VoiceChannel)):
                em.add_field(name=ctx.t('commons.channel'), value='{0.mention}\n`{0.id}`'.format(target))

        em.add_field(name=ctx.t('commons.moderator'),
                     value='{0} ({0.mention})\n`{0.id}`'.format(kwargs['moderator']))

        if reason:
            em.add_field(name=ctx.t('commons.reason'), value=reason, inline=False)

        log_message = await logs.send(embed=em)
        await self.disco.db.register_mod_log(action=ctx.command.name, case_id=case_id, moderator_id=ctx.author.id,
                                             guild_id=ctx.guild.id, channel_id=logs.id, message_id=log_message.id)

    @commands.command(name='reason')
    @commands.cooldown(1, 5, commands.BucketType.member)
    @checks.mod_role_or_permission('manage_messages')
    async def _reason(self, ctx, case_id, *, reason):
        if case_id[0] == '#':
            case_id = case_id[1:]
        if not case_id.isdecimal() or not 999 < (case_id := int(case_id)) < 999999999:
            raise commands.UserInputError

        log = await self.disco.db.get_mod_log(ctx.guild.id, case_id)
        if log is None:
            return await ctx.send(ctx.t('commands.reason.notFound', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name}))
        if log.moderator_id != ctx.author.id:
            return await ctx.send(ctx.t('commands.reason.notAuthor', {"emoji": self.disco.emoji["false"],
                                                                      "author": ctx.author.name}))

        channel = ctx.guild.get_channel(log.channel_id)
        if channel is None:
            return await ctx.send(ctx.t('commands.reason.channelNotFound', {"emoji": self.disco.emoji["false"],
                                                                            "author": ctx.author.name}))

        permissions = channel.permissions_for(ctx.me)
        missing = []
        if not permissions.manage_messages:
            missing.append('manage_messages')
        if not permissions.read_message_history:
            missing.append('read_message_history')

        if missing:
            raise commands.BotMissingPermissions(missing)

        try:
            message = await channel.fetch_message(log.message_id)
        except discord.NotFound:
            return await ctx.send(ctx.t('commands.reason.messageNotFound', {"emoji": self.disco.emoji["false"],
                                                                            "author": ctx.author.name}))

        em = message.embeds[0]
        if log.action == 'clean' and message.edited_at is None:
            em.add_field(name=ctx.t('commons.reason'), value=reason[:1024], inline=False)
        else:
            em.set_field_at(len(em.fields) - 1, name=ctx.t('commons.reason'), value=reason[:1024])

        await message.edit(content=message.content, embed=em)

        await ctx.send(ctx.t('commands.reason.success', {"emoji": self.disco.emoji["true"],
                                                         "author": ctx.author.name,
                                                         "id": log.id}))

    @commands.command(name='ban')
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(2, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('ban_members')
    @checks.is_below_mod_threshold()
    async def _ban(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        if not members:
            return await ctx.send(ctx.t('commands.ban.noMentions', {"author": ctx.author.name,
                                                                    "emoji": self.disco.emoji["false"]}))
        if reason is None:
            reason = ctx.t('commands.ban.reasonNotSpecified')

        reason_ = f'{ctx.author} - {ctx.author.id}: {reason}'[:512]
        final_targets = list(set(members))[:5]
        bans = []
        for member in final_targets[:ctx.action_threshold - ctx.daily_action_count if ctx.action_threshold else None]:
            if member.top_role >= ctx.author.top_role or member.top_role > ctx.me.top_role:
                continue

            try:
                await member.ban(reason=reason_, delete_message_days=7)
            except discord.Forbidden:
                pass
            else:
                bans.append(member)
                self.disco.loop.create_task(self._mod_log(ctx, user=member, moderator=ctx.author, reason=reason,
                                                          colour=0xdb0417))

        emoji = self.disco.emoji["true"]
        successfully = ctx.t('commands.ban.successfully')
        await ctx.send('\n'.join(successfully.format(emoji=emoji, member=member.mention) for member in bans)
                       + (ctx.t('commands.ban.invalidMembers', {"emoji": self.disco.emoji["alert"],
                                                                "members": len(final_targets) - len(bans)})
                          if not final_targets or bans != final_targets else ''))

    @commands.command(name='kick')
    @commands.bot_has_permissions(kick_members=True)
    @commands.cooldown(2, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('kick_members')
    @checks.is_below_mod_threshold()
    async def _kick(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        if not members:
            return await ctx.send(ctx.t('commands.kick.noMentions', {"author": ctx.author.name,
                                                                     "emoji": self.disco.emoji["false"]}))
        if reason is None:
            reason = ctx.t('commands.kick.reasonNotSpecified')

        reason_ = f'{ctx.author} - {ctx.author.id}: {reason}'[:512]
        final_targets = list(set(members))[:5]
        kicks = []
        for member in final_targets[:ctx.action_threshold - ctx.daily_action_count if ctx.action_threshold else None]:
            if member.top_role >= ctx.author.top_role or member.top_role > ctx.me.top_role:
                continue

            try:
                await member.kick(reason=reason_)
            except discord.Forbidden:
                pass
            else:
                kicks.append(member)
                self.disco.loop.create_task(self._mod_log(ctx, user=member, moderator=ctx.author, reason=reason,
                                                          colour=0x3b58ff))

        emoji = self.disco.emoji["true"]
        successfully = ctx.t('commands.kick.successfully')
        await ctx.send('\n'.join(successfully.format(emoji=emoji, member=member.mention) for member in kicks)
                       + (ctx.t('commands.kick.invalidMembers', {"emoji": self.disco.emoji["alert"],
                                                                 "members": len(final_targets) - len(kicks)})
                          if not final_targets or kicks != final_targets else ''))

    @commands.command(name='softban', aliases=['sban'])
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(2, 12, commands.BucketType.guild)
    @checks.mod_role_or_permission('ban_members')
    @checks.is_below_mod_threshold()
    async def _soft_ban(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        if not members:
            return await ctx.send(ctx.t('commands.softban.noMentions', {"author": ctx.author.name,
                                                                        "emoji": self.disco.emoji["false"]}))
        if reason is None:
            reason = ctx.t('commands.softban.reasonNotSpecified')

        reason_ = f'{ctx.author} - {ctx.author.id}: {reason}'[:512]
        final_targets = list(set(members))[:5]
        soft_bans = []
        for member in final_targets[:ctx.action_threshold - ctx.daily_action_count if ctx.action_threshold else None]:
            if member.top_role >= ctx.author.top_role or member.top_role > ctx.me.top_role:
                continue

            try:
                await member.ban(reason=reason_, delete_message_days=7)
                await member.unban(reason=reason_)
            except discord.Forbidden:
                pass
            else:
                soft_bans.append(member)
                self.disco.loop.create_task(self._mod_log(ctx, user=member, moderator=ctx.author, reason=reason,
                                                          colour=0xff051b))

        emoji = self.disco.emoji["true"]
        successfully = ctx.t('commands.softban.successfully')
        await ctx.send('\n'.join(successfully.format(emoji=emoji, member=member.mention) for member in soft_bans)
                       + (ctx.t('commands.softban.invalidMembers', {"emoji": self.disco.emoji["alert"],
                                                                    "members": len(final_targets) - len(soft_bans)})
                          if not final_targets or soft_bans != final_targets else ''))

    @commands.command(name='forceban')
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(2, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('ban_members')
    @checks.is_below_mod_threshold('ban')
    async def _force_ban(self, ctx, user_id: int, *, reason=None):
        if (user := ctx.guild.get_member(user_id)) and (user.top_role >= ctx.author.top_role
                                                        or user.top_role >= ctx.me.top_role):
            return await ctx.send(ctx.t('commands.forceban.higherRole', {"emoji": self.disco.emoji["false"],
                                                                         "author": ctx.author.member,
                                                                         "member": user}))
        else:
            if (user := self.disco.get_user(user_id)) is None:
                try:
                    user = await self.disco.fetch_user(user_id)
                except discord.NotFound:
                    return await ctx.send(ctx.t('commands.forceban.userNotFound', {"emoji": self.disco.emoji["false"],
                                                                                   "author": ctx.author.name}))

            try:
                ban = await ctx.guild.fetch_ban(user)
            except discord.NotFound:
                pass
            else:
                return await ctx.send(ctx.t('commands.forceban.alreadyBanned', {"emoji": self.disco.emoji["false"],
                                                                                "author": ctx.author.name,
                                                                                "user": user,
                                                                                "reason": ban.reason}))

        if reason is None:
            reason = ctx.t('commands.forceban.reasonNotSpecified')

        await ctx.guild.ban(user, reason=f'{ctx.author} - {ctx.author.id}: {reason}'[:512], delete_message_days=7)
        self.disco.loop.create_task(self._mod_log(ctx, user=user, moderator=ctx.author, reason=reason, colour=0xba0010))

        await ctx.send(ctx.t('commands.forceban.success', {"emoji": self.disco.emoji["true"],
                                                           "author": ctx.author.name,
                                                           "user": user}))

    @commands.command(name='unban')
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(2, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('ban_members')
    @checks.is_below_mod_threshold()
    async def _unban(self, ctx, user_id: int, *, reason=None):
        if (user := self.disco.get_user(user_id)) is None:
            try:
                user = await self.disco.fetch_user(user_id)
            except discord.NotFound:
                return await ctx.send(ctx.t('commands.unban.userNotFound', {"emoji": self.disco.emoji["false"],
                                                                            "author": ctx.author.name}))

        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            return await ctx.send(ctx.t('commands.unban.notBanned', {"emoji": self.disco.emoji["false"],
                                                                     "author": ctx.author.name,
                                                                     "user": user}))

        if reason is None:
            reason = ctx.t('commands.unban.reasonNotSpecified')

        await ctx.guild.unban(user, reason=f'{ctx.author} - {ctx.author.id}: {reason}'[:512])
        self.disco.loop.create_task(self._mod_log(ctx, user=user, moderator=ctx.author, reason=reason, colour=0xdb09a3))

        await ctx.send(ctx.t('commands.unban.success', {"emoji": self.disco.emoji["true"],
                                                        "author": ctx.author.name,
                                                        "user": user}))

    @commands.command(name='clean', aliases=['purge'])
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @commands.cooldown(3, 12, commands.BucketType.guild)
    @checks.mod_role_or_permission('manage_messages')
    @checks.is_below_mod_threshold()
    async def _clean(self, ctx, amount: typing.Optional[int] = 100,
                     channel: typing.Optional[discord.TextChannel] = None,
                     member: typing.Optional[discord.Member] = None, *, content=None):
        if not 0 < amount < 101:
            return await ctx.send(ctx.t('commands.clean.invalidAmount', {"emoji": self.disco.emoji["false"],
                                                                         "author": ctx.author.name}))

        if channel is None:
            channel = ctx.channel
        else:
            permissions = channel.permissions_for(ctx.me)
            missing = []
            if not permissions.manage_messages:
                missing.append('manage_messages')
            if not permissions.read_message_history:
                missing.append('read_message_history')

            if missing:
                raise commands.BotMissingPermissions(missing)

        try:
            deleted = await channel.purge(limit=amount + 1, check=lambda m: (m.author == member if member else True)
                                                                            and (content in m.content
                                                                                 if content and m.content else True))
        except discord.Forbidden:
            raise commands.BotMissingPermissions(['manage_messages', 'read_message_history'])

        deleted = len(deleted) - 1

        self.disco.loop.create_task(self._mod_log(ctx, targets=[member, channel], moderator=ctx.author, amount=deleted,
                                                  channel=channel.mention, colour=0xffe017))

        await ctx.send(ctx.t('commands.clean.successWithMember' if member else 'commands.clean.success',
                             {"emoji": self.disco.emoji["true"],
                              "author": ctx.author.name,
                              "amount": deleted,
                              "member": member,
                              "channel": channel.mention}),
                       delete_after=8)


def setup(disco):
    disco.add_cog(Moderation(disco))
