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


class Checks:
    @staticmethod
    def staffer_or_dj_role():
        async def predicate(ctx):
            role = ctx.guild.get_role(ctx.gdb.options['dj_role'])
            if ctx.author.guild_permissions.manage_guild or role in ctx.author.roles:
                return True

            raise commands.errors.MissingRole([role])

        return commands.check(predicate)

    @staticmethod
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

    @staticmethod
    def ensure_voice_connection():
        async def predicate(ctx):
            if not ctx.command._before_invoke:
                ctx.command._before_invoke = before_play

            return True

        return commands.check(predicate)

    @staticmethod
    def requires_user_choices():
        async def predicate(ctx):
            if ctx.author.id in ctx.bot._waiting_for_choice:
                raise WaitingForPreviousChoice((ctx.t('errors.waitingForPreviousChoice', {
                    "author": ctx.author.name, "emoji": ctx.bot.emoji["false"]})))

            ctx._remove_from_waiting = True

            return True

        return commands.check(predicate)
