from discord.ext import commands
from .errors import MusicError
from .locale import l

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
                raise MusicError(l(ctx, 'errors.notConnected') % (
                    ctx.bot.emoji["false"], ctx.author.name))

            if not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
                raise MusicError(l(ctx, 'errors.notSameVoiceChannel') % (
                    ctx.bot.emoji["false"], ctx.author.name))

            ctx.player = ctx.cog.get_player(ctx.guild.id)

            return True

        return commands.check(predicate)

    @staticmethod
    async def before_play(cog, ctx):
        if ctx.author.id in cog.waiting:
            raise MusicError(l(ctx, 'errors.waitingForPreviousChoice') % (
                    ctx.bot.emoji["false"], ctx.author.name))

        ctx.player = player = cog.get_player(ctx.guild.id)
        if not ctx.me.voice:
            if not ctx.author.voice:
                raise MusicError(l(ctx, 'errors.userNotVoiceConnected') % (
                    ctx.bot.emoji["false"], ctx.author.name))

            vc = ctx.author.voice.channel
            perms = vc.permissions_for(ctx.me)

            if not perms.connect or not perms.speak:
                raise MusicError(l(ctx, 'errors.notEnoughPermissionsToJoin') % (
                    ctx.bot.emoji["false"], ctx.author.name))

            if vc.user_limit and len(vc.members) + 1 > vc.user_limit and not perms.administrator:
                raise MusicError(l(ctx, 'errors.fullVoiceChannel') % (
                    ctx.bot.emoji["false"], ctx.author.name))

            player.text_channel = ctx.channel
            player.locale = ctx.locale
            await player.connect(vc.id)
            await ctx.send(l(ctx, 'commands.play.connected') % (
                    ctx.bot.emoji["wireless"], vc))

        elif not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
            raise MusicError(l(ctx, 'errors.notSameVoiceChannel') % (
                    ctx.bot.emoji["false"], ctx.author.name))

        elif player.size > 1499:
            raise MusicError(l(ctx, 'errors.fullQueue') % (
                    ctx.bot.emoji["false"], ctx.author.name))

        return True