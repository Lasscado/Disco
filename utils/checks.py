from discord.ext import commands
from .errors import MusicError
from .locale import l

async def before_play(cog, ctx):
    if ctx.author.id in cog.waiting:
        raise MusicError(l(ctx, 'errors.waitingForPreviousChoice', {"author": ctx.author.name,
            "emoji": ctx.bot.emoji["false"]}))

    ctx.player = player = cog.get_player(ctx.guild.id)
    if not ctx.me.voice:
        if not ctx.author.voice:
            raise MusicError(l(ctx, 'errors.userNotVoiceConnected', {"author": ctx.author.name,
                "emoji": ctx.bot.emoji["false"]}))

        vc = ctx.author.voice.channel
        perms = vc.permissions_for(ctx.me)

        if not perms.connect or not perms.speak:
            raise MusicError(l(ctx, 'errors.notEnoughPermissionsToJoin', {
                "emoji": ctx.bot.emoji["false"], "author": ctx.author.name}))

        if vc.user_limit and len(vc.members) + 1 > vc.user_limit and not perms.administrator:
            raise MusicError(l(ctx, 'errors.fullVoiceChannel', {"author": ctx.author.name,
                "emoji": ctx.bot.emoji["false"]}))

        player.text_channel = ctx.channel
        player.locale = ctx.locale
        await player.connect(vc.id)
        await ctx.send(l(ctx, 'commands.play.connected', {"channel": vc,
            "emoji": ctx.bot.emoji["wireless"]}))

        default_vol = ctx._guild.data['options']['defaultVolume']
        if default_vol is not None:
            await player.set_volume(default_vol)

    elif not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
        raise MusicError(l(ctx, 'errors.notSameVoiceChannel', {"author": ctx.author.name,
            "emoji": ctx.bot.emoji["false"]}))

    elif player.size > 1499:
        raise MusicError(l(ctx, 'errors.fullQueue', {"author": ctx.author.name,
            "emoji": ctx.bot.emoji["false"]}))

    return True

class Checks:
    @staticmethod
    def staffer_or_dj_role():
        async def predicate(ctx):
            role = ctx.guild.get_role(ctx._guild.data['options']['djRole'])
            if ctx.author.guild_permissions.manage_guild or role in ctx.author.roles:
                return True

            raise commands.errors.MissingRole([role])

        return commands.check(predicate)

    @staticmethod
    def is_voice_connected():
        async def predicate(ctx):
            if not ctx.me.voice:
                raise MusicError(l(ctx, 'errors.notConnected', {"author": ctx.author.name,
                    "emoji": ctx.bot.emoji["false"]}))

            if not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
                raise MusicError(l(ctx, 'errors.notSameVoiceChannel', {"author": ctx.author.name,
                    "emoji": ctx.bot.emoji["false"]}))

            ctx.player = ctx.cog.get_player(ctx.guild.id)

            return True

        return commands.check(predicate)

    @staticmethod
    def ensure_voice_connection():
        async def predicate(ctx):
            if not ctx.command._before_invoke:
                ctx.command._before_invoke = before_play

            return True

        return commands.check(predicate)