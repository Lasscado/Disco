from discord.ext.commands.errors import CommandError


class DiscoError(CommandError):
    pass


class MusicError(DiscoError):
    '''Erro padrão para o módulo de Música'''
    pass
