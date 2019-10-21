import typing

import discord
from discord.ext import commands

from utils import checks, TimeConverter


class Moderation(commands.Cog):
    def __init__(self, disco):
        self.disco = disco

    @commands.command(name='ban')
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('ban_members')
    async def _ban(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        if reason is None:
            reason = ctx.t('commands.ban.reasonNotSpecified')

        final_targets = list(set(members))[:10]
        bans = []
        for member in final_targets:
            if member.top_role >= ctx.author.role or member.top_role > ctx.me.top_role:
                continue

            try:
                await member.ban(reason=f'{ctx.author} - {ctx.author.id}: {reason}'[:512], delete_message_days=7)
            except discord.Forbidden:
                pass
            else:
                bans.append(member)

        emoji = self.disco.emoji["true"]
        successfully = ctx.t('commands.ban.successfully')
        await ctx.send('\n'.join(successfully.format(emoji=emoji, member=member.mention) for member in bans)
                       + (ctx.t('commands.ban.invalidMembers', {"emoji": self.disco.emoji["alert"],
                                                                "members": len(final_targets) - len(bans)})
                          if not final_targets or bans != final_targets else ''))

    @commands.command(name='kick')
    @commands.bot_has_permissions(kick_members=True)
    @commands.cooldown(1, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('kick_members')
    async def _kick(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        if reason is None:
            reason = ctx.t('commands.kick.reasonNotSpecified')

        final_targets = list(set(members))[:10]
        kicks = []
        for member in final_targets:
            if member.top_role >= ctx.author.role or member.top_role > ctx.me.top_role:
                continue

            try:
                await member.kick(reason=f'{ctx.author} - {ctx.author.id}: {reason}'[:512], delete_message_days=7)
            except discord.Forbidden:
                pass
            else:
                kicks.append(member)

        emoji = self.disco.emoji["true"]
        successfully = ctx.t('commands.kick.successfully')
        await ctx.send('\n'.join(successfully.format(emoji=emoji, member=member.mention) for member in kicks)
                       + (ctx.t('commands.kick.invalidMembers', {"emoji": self.disco.emoji["alert"],
                                                                 "members": len(final_targets) - len(kicks)})
                          if not final_targets or kicks != final_targets else ''))

    @commands.command(name='softban', aliases=['sban'])
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 15, commands.BucketType.guild)
    @checks.mod_role_or_permission('ban_members')
    async def _soft_ban(self, ctx, members: commands.Greedy[discord.Member], *, reason=None):
        if reason is None:
            reason = ctx.t('commands.softban.reasonNotSpecified')

        final_targets = list(set(members))[:10]
        soft_bans = []
        for member in final_targets:
            if member.top_role >= ctx.author.role or member.top_role > ctx.me.top_role:
                continue

            try:
                await member.ban(reason=f'{ctx.author} - {ctx.author.id}: {reason}'[:512], delete_message_days=7)
                await member.unban(reason=f'{ctx.author} - {ctx.author.id}: {reason}'[:512])
            except discord.Forbidden:
                pass
            else:
                soft_bans.append(member)

        emoji = self.disco.emoji["true"]
        successfully = ctx.t('commands.softban.successfully')
        await ctx.send('\n'.join(successfully.format(emoji=emoji, member=member.mention) for member in soft_bans)
                       + (ctx.t('commands.softban.invalidMembers', {"emoji": self.disco.emoji["alert"],
                                                                    "members": len(final_targets) - len(soft_bans)})
                          if not final_targets or soft_bans != final_targets else ''))

    @commands.command(name='forceban')
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('ban_members')
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

        await ctx.send(ctx.t('commands.forceban.success', {"emoji": self.disco.emoji["true"],
                                                           "author": ctx.author.name,
                                                           "user": user}))

    @commands.command(name='unban')
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('ban_members')
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

        await ctx.send(ctx.t('commands.unban.success', {"emoji": self.disco.emoji["true"],
                                                        "author": ctx.author.name,
                                                        "user": user}))

    @commands.command(name='clean', aliases=['purge'])
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    @commands.cooldown(1, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('manage_messages')
    async def _clean(self, ctx, amount: typing.Optional[int] = 100,
                     channel: typing.Optional[discord.TextChannel] = None,
                     member: typing.Optional[discord.Member] = None, content=None):
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
            deleted = await channel.purge(limit=amount, check=lambda m: (m.author == member if member else True)
                                          and (content in m.content if content and m.content else True))
        except discord.Forbidden:
            raise commands.BotMissingPermissions(['manage_messages', 'read_message_history'])

        await ctx.send(ctx.t('commands.clean.successWithMember' if member else 'commands.clean.success',
                             {"emoji": self.disco.emoji["true"],
                              "author": ctx.author.name,
                              "amount": len(deleted),
                              "member": member,
                              "channel": channel.mention}))

    @commands.command(name='mute')
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 6, commands.BucketType.guild)
    @checks.mod_role_or_permission('manage_roles')
    async def _mute(self, ctx, members: commands.Greedy[discord.Member], *, extra: TimeConverter):
        pass


def setup(disco):
    disco.add_cog(Moderation(disco))
