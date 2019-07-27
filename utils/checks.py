from discord.ext import commands
from .errors import MusicError


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
                raise MusicError(f'{ctx.bot.emoji["false"]} **{ctx.author.name}**, eu não estou '
                    'conectado em nenhum canal de voz.')

            if not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
                raise MusicError(f'{ctx.bot.emoji["false"]} **{ctx.author.name}**, você precisa '
                    'estar conectado ao meu canal de voz para usar esse comando.')

            ctx.player = ctx.cog.get_player(ctx.guild.id)

            return True

        return commands.check(predicate)

    @staticmethod
    async def before_play(cog, ctx):
        if ctx.author.id in cog.waiting:
            raise MusicError(f'{ctx.bot.emoji["false"]} **{ctx.author.name}**, você ainda não '
                'selecionou uma faixa no comando anterior!')

        ctx.player = player = cog.get_player(ctx.guild.id)
        if not ctx.me.voice:
            if not ctx.author.voice:
                raise MusicError(f'{ctx.bot.emoji["false"]} **{ctx.author.name}**, '
                    'você precisa estar conectado em um canal de voz para usar esse comando.')

            vc = ctx.author.voice.channel
            perms = vc.permissions_for(ctx.me)

            if not perms.connect or not perms.speak:
                raise MusicError(f'{ctx.bot.emoji["false"]} **{ctx.author.name}**, '
                    'eu preciso das permissões **`CONECTAR`** e **`FALAR`** no seu canal de voz.')

            if vc.user_limit and len(vc.members) + 1 > vc.user_limit and not perms.administrator:
                raise MusicError(f'{ctx.bot.emoji["false"]} **{ctx.author.name}**, '
                    'seu canal de voz está lotado!')

            player.text_channel = ctx.channel
            await player.connect(vc.id)
            await ctx.send(f'{ctx.bot.emoji["wireless"]} Me conectei ao canal de voz **`{vc}`**.')

        elif not ctx.author.voice or ctx.author.voice.channel.id != ctx.me.voice.channel.id:
            raise MusicError(f'{ctx.bot.emoji["false"]} **{ctx.author.name}**, você precisa '
                'estar conectado ao meu canal de voz para usar esse comando.')

        elif player.size > 1499:
            raise MusicError(f'{ctx.bot.emoji["false"]} **{ctx.author.name}**, a fila '
                'de reprodução desse servidor está lotada! Remova alguma faixa ou tente '
                'novamente mais tarde.')

        return True