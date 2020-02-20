from datetime import datetime, timedelta

from babel.dates import format_timedelta
from discord.ext import commands

from .constants import PATREON_DONATE_URL
from .errors import *


async def before_play(cog, ctx):
    if not any(n for n in ctx.bot.wavelink.nodes.values() if n.is_available):
        raise MusicError(ctx.t('errors.noMusicNodesAvailable', {"author": ctx.author.name,
                                                                "emoji": ctx.bot.emoji["false"],
                                                                "donate": PATREON_DONATE_URL}))

    ctx.player = player = ctx.bot.get_player(ctx.guild.id)
    if not ctx.me.voice:
        if not ctx.author.voice:
            raise MusicError(ctx.t('errors.userNotVoiceConnected', {"author": ctx.author.name,
                                                                    "emoji": ctx.bot.emoji["false"]}))

        vc = ctx.author.voice.channel
        perms = vc.permissions_for(ctx.me)

        if not perms.connect or not perms.speak:
            raise MusicError(ctx.t('errors.notEnoughPermissionsToJoin', {
                "emoji": ctx.bot.emoji["false"], "author": ctx.author.name}))

        if vc.user_limit and len(vc.members) + 1 > vc.user_limit and not perms.administrator:
            raise MusicError(ctx.t('errors.fullVoiceChannel', {"author": ctx.author.name,
                                                               "emoji": ctx.bot.emoji["false"]}))

        player.text_channel = ctx.channel
        player.t = ctx.t
        await player.connect(vc.id)
        await ctx.send(ctx.t('commands.play.connected', {"channel": vc,
                                                         "emoji": ctx.bot.emoji["wireless"]}))

        default_vol = ctx.gdb.options['default_volume']
        if default_vol is not None:
            await player.set_volume(default_vol)

    elif not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
        raise MusicError(ctx.t('errors.notSameVoiceChannel', {"author": ctx.author.name,
                                                              "emoji": ctx.bot.emoji["false"]}))

    elif player.size > 1499:
        raise MusicError(ctx.t('errors.fullQueue', {"author": ctx.author.name,
                                                    "emoji": ctx.bot.emoji["false"]}))

    return True


def is_below_mod_threshold(action=None):
    async def predicate(ctx):
        action_ = action or ctx.command.name
        if threshold := ctx.gdb.options['mod_threshold'][action_]:
            if (count := await ctx.bot.db.total_daily_mod_logs(action_, ctx.guild.id, ctx.author.id)) > threshold:
                if last_action := await ctx.bot.db.get_last_mod_log(action=action_, guild_id=ctx.guild.id,
                                                                    moderator_id=ctx.author.id):
                    next_use = format_timedelta(datetime.utcnow() - (datetime.utcfromtimestamp(last_action.date)
                                                                     + timedelta(days=1)),
                                                locale=ctx.gdb.options['locale'])
                else:
                    next_use = ctx.t('commons.unknownEta')

                raise DiscoError(ctx.t('errors.hitModThreshold', {"emoji": ctx.bot.emoji["false"],
                                                                  "author": ctx.author.name,
                                                                  "action": action_,
                                                                  "threshold": threshold,
                                                                  "count": count,
                                                                  "next": next_use}))

            ctx.daily_action_count = count
        ctx.action_threshold = threshold

        return True

    return commands.check(predicate)


def mod_role_or_permission(permission):
    async def predicate(ctx):
        if getattr(ctx.author.guild_permissions, permission) or \
                ctx.guild.get_role(ctx.gdb.options['mod_role']) in ctx.author.roles:
            return True

        raise commands.errors.MissingPermissions([permission])

    return commands.check(predicate)


def staffer_or_dj_role():
    async def predicate(ctx):
        role = ctx.guild.get_role(ctx.gdb.options['dj_role'])
        if ctx.author.guild_permissions.manage_guild or role in ctx.author.roles:
            return True

        raise commands.errors.MissingRole([role])

    return commands.check(predicate)


def is_voice_connected():
    async def predicate(ctx):
        if not ctx.me.voice:
            raise MusicError(ctx.t('errors.notConnected', {"author": ctx.author.name,
                                                           "emoji": ctx.bot.emoji["false"]}))

        if not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
            raise MusicError(ctx.t('errors.notSameVoiceChannel', {"author": ctx.author.name,
                                                                  "emoji": ctx.bot.emoji["false"]}))

        ctx.player = ctx.bot.get_player(ctx.guild.id)

        return True

    return commands.check(predicate)


def ensure_voice_connection():
    async def predicate(ctx):
        if not ctx.command._before_invoke:
            ctx.command._before_invoke = before_play

        return True

    return commands.check(predicate)
